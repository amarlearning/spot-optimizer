import os
import pytest
import threading
from unittest.mock import Mock, patch
import pandas as pd
from spot_optimizer.spot_optimizer import SpotOptimizer
from spot_optimizer.optimizer_mode import Mode


@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    with patch("spot_optimizer.spot_optimizer.user_data_dir") as mock_dir:
        mock_dir.return_value = str(tmp_path)
        yield tmp_path


@pytest.fixture
def mock_db():
    db = Mock()
    db.connect = Mock()
    db.disconnect = Mock()
    return db


@pytest.fixture
def mock_advisor():
    return Mock()


@pytest.fixture
def optimizer(mock_db, mock_advisor, mock_data_dir):
    with patch("spot_optimizer.spot_optimizer.DuckDBStorage") as mock_db_class, patch(
        "spot_optimizer.spot_optimizer.AwsSpotAdvisorData"
    ) as mock_advisor_class:
        mock_db_class.return_value = mock_db
        mock_advisor_class.return_value = mock_advisor
        optimizer = SpotOptimizer()
        yield optimizer


def test_default_db_path(mock_data_dir):
    """Test that default database path is created correctly."""
    expected_path = os.path.join(str(mock_data_dir), "spot_advisor_data.db")
    assert SpotOptimizer.get_default_db_path() == expected_path
    assert os.path.dirname(expected_path) == str(mock_data_dir)


def test_singleton_pattern():
    """Test that SpotOptimizer follows singleton pattern."""
    first = SpotOptimizer.get_instance()
    second = SpotOptimizer.get_instance()
    assert first is second
    # Clean up singleton for other tests
    SpotOptimizer.reset_instance()


def test_initialization(optimizer, mock_db):
    """Test optimizer initialization."""
    assert optimizer.db is mock_db
    mock_db.connect.assert_called_once()


def test_cleanup(mock_db, mock_advisor):
    """Test database cleanup method."""
    optimizer = SpotOptimizer()
    optimizer.db = mock_db
    optimizer.cleanup()
    mock_db.disconnect.assert_called_once()
    assert optimizer.db is None


@pytest.fixture
def sample_query_result():
    return pd.DataFrame(
        {
            "instance_type": ["m5.xlarge"],
            "cores": [4],
            "ram_gb": [16],
            "spot_score": [75],
            "interruption_rate": [1],
            "instances_needed": [2],
            "total_cores": [8],
            "total_memory": [32],
            "cpu_waste_pct": [0],
            "memory_waste_pct": [0],
        }
    )


def test_optimize_success(optimizer, mock_db, sample_query_result):
    """Test successful optimization with valid parameters."""
    mock_db.query_data.return_value = sample_query_result

    result = optimizer.optimize(
        cores=8, memory=32, region="us-west-2", ssd_only=False, arm_instances=True
    )

    assert result == {
        "instances": {"type": "m5.xlarge", "count": 2},
        "mode": "balanced",
        "total_cores": 8,
        "total_ram": 32,
        "reliability": {"spot_score": 75, "interruption_rate": 1},
    }


def test_optimize_no_results(optimizer, mock_db):
    """Test optimization when no suitable instances are found."""
    mock_db.query_data.return_value = pd.DataFrame()

    with pytest.raises(
        ValueError,
        match="No suitable instances found matching for cpu = 8 and memory = 32 and region = us-west-2 and mode = balanced",
    ):
        optimizer.optimize(cores=8, memory=32)


def test_optimize_with_instance_family(optimizer, mock_db, sample_query_result):
    """Test optimization with instance family filter."""
    mock_db.query_data.return_value = sample_query_result

    result = optimizer.optimize(cores=8, memory=32, instance_family=["m5", "c5"])

    # Verify the result
    assert result["instances"]["type"] == "m5.xlarge"
    # Verify that the query included instance family filter
    query_call = mock_db.query_data.call_args[0][0]
    assert "instance_family IN" in query_call


def test_optimize_with_ssd_only(optimizer, mock_db, sample_query_result):
    """Test optimization with SSD-only filter."""
    mock_db.query_data.return_value = sample_query_result

    result = optimizer.optimize(cores=8, memory=32, ssd_only=True)

    # Verify the query included SSD filter
    query_call = mock_db.query_data.call_args[0][0]
    assert "storage_type = 'ssd'" in query_call


def test_optimize_with_arm_instances(optimizer, mock_db, sample_query_result):
    """Test optimization with ARM instances disabled."""
    mock_db.query_data.return_value = sample_query_result

    result = optimizer.optimize(cores=8, memory=32, arm_instances=False)

    # Verify the query excluded ARM instances
    query_call = mock_db.query_data.call_args[0][0]
    assert "architecture != 'arm64'" in query_call


@pytest.mark.parametrize(
    "mode", [Mode.LATENCY.value, Mode.BALANCED.value, Mode.FAULT_TOLERANCE.value]
)
def test_optimize_different_modes(optimizer, mock_db, sample_query_result, mode):
    """Test optimization with different modes."""
    mock_db.query_data.return_value = sample_query_result

    result = optimizer.optimize(cores=8, memory=32, mode=mode)

    assert result["mode"] == mode


def test_optimize_database_error(optimizer, mock_db):
    """Test handling of database errors."""
    mock_db.query_data.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        optimizer.optimize(cores=8, memory=32)


def test_optimize_invalid_parameters(optimizer):
    """Test optimization with invalid parameters."""
    with pytest.raises(ValueError):
        optimizer.optimize(cores=-1, memory=32)

    with pytest.raises(ValueError):
        optimizer.optimize(cores=8, memory=-1)


def test_thread_safety():
    """Test that singleton pattern is thread-safe."""
    SpotOptimizer.reset_instance()
    instances = []

    def get_instance():
        instances.append(SpotOptimizer.get_instance())

    # Create multiple threads that try to get the instance
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=get_instance)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All instances should be the same object
    first_instance = instances[0]
    for instance in instances:
        assert instance is first_instance

    # Clean up
    SpotOptimizer.reset_instance()


def test_context_manager(mock_db, mock_advisor, mock_data_dir):
    """Test context manager functionality."""
    with patch("spot_optimizer.spot_optimizer.DuckDBStorage") as mock_db_class, patch(
        "spot_optimizer.spot_optimizer.AwsSpotAdvisorData"
    ) as mock_advisor_class:
        mock_db_class.return_value = mock_db
        mock_advisor_class.return_value = mock_advisor

        with SpotOptimizer() as optimizer:
            assert optimizer.db is mock_db
            mock_db.connect.assert_called_once()

        # After exiting context, cleanup should be called
        mock_db.disconnect.assert_called_once()


def test_reset_instance_functionality():
    """Test that reset_instance properly cleans up and resets the singleton."""
    # Get an instance
    first_instance = SpotOptimizer.get_instance()

    # Reset the instance
    SpotOptimizer.reset_instance()

    # Get a new instance - should be different from the first one
    second_instance = SpotOptimizer.get_instance()

    # Should be different objects (new instance created)
    assert first_instance is not second_instance

    # Clean up
    SpotOptimizer.reset_instance()


def test_cleanup_with_exception(mock_db, mock_advisor):
    """Test that cleanup handles exceptions gracefully."""
    optimizer = SpotOptimizer()
    optimizer.db = mock_db

    # Make disconnect raise an exception
    mock_db.disconnect.side_effect = Exception("Database disconnect error")

    # Should not raise an exception
    optimizer.cleanup()

    # DB should be set to None despite the error
    assert optimizer.db is None


def test_cleanup_idempotent():
    """Test that cleanup can be called multiple times safely."""
    optimizer = SpotOptimizer()

    # First cleanup
    optimizer.cleanup()
    assert optimizer.db is None

    # Second cleanup should not raise an error
    optimizer.cleanup()
    assert optimizer.db is None

import os
import pytest
import threading
from unittest.mock import Mock, patch
from spot_optimizer.spot_optimizer import SpotOptimizerFacade
from spot_optimizer.exceptions import OptimizationError, ValidationError


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
def mock_engine():
    engine = Mock()
    engine.ensure_fresh_data = Mock()
    return engine


@pytest.fixture
def mock_core():
    core = Mock()
    core.optimize = Mock()
    return core


@pytest.fixture
def facade(mock_db, mock_advisor, mock_engine, mock_core):
    """Fixture for SpotOptimizerFacade with mocked dependencies."""
    with patch(
        "spot_optimizer.spot_optimizer.SpotOptimizerFacade.create_default"
    ) as mock_create_default:
        facade_instance = SpotOptimizerFacade(
            spot_advisor=mock_advisor,
            db=mock_db,
            engine=mock_engine,
            core=mock_core,
        )
        mock_create_default.return_value = facade_instance
        yield facade_instance


def test_default_db_path(mock_data_dir):
    """Test that default database path is created correctly."""
    expected_path = os.path.join(str(mock_data_dir), "spot_advisor_data.db")
    assert SpotOptimizerFacade.get_default_db_path() == expected_path
    assert os.path.dirname(expected_path) == str(mock_data_dir)


def test_singleton_pattern():
    """Test that SpotOptimizerFacade follows singleton pattern."""
    first = SpotOptimizerFacade.get_instance()
    second = SpotOptimizerFacade.get_instance()
    assert first is second
    SpotOptimizerFacade.reset_instance()


def test_initialization_with_dependencies(
    facade, mock_advisor, mock_db, mock_engine, mock_core
):
    """Test facade initialization with injected dependencies."""
    assert facade.spot_advisor is mock_advisor
    assert facade.db is mock_db
    assert facade.engine is mock_engine
    assert facade.core is mock_core


def test_context_manager_connects_and_disconnects(facade, mock_db):
    """Test that context manager handles DB connection."""
    with facade as f:
        assert f is facade
        mock_db.connect.assert_called_once()
    mock_db.disconnect.assert_called_once()


def test_optimize_success(facade, mock_engine, mock_core):
    """Test successful optimization call through the facade."""
    mock_result = {
        "instances": {"type": "m5.large", "count": 2},
        "total_cores": 8,
        "total_ram": 32,
    }
    mock_core.optimize.return_value = mock_result

    result = facade.optimize(cores=8, memory=32)

    mock_engine.ensure_fresh_data.assert_called_once()
    mock_core.optimize.assert_called_once_with(
        cores=8,
        memory=32,
        region="us-west-2",
        ssd_only=False,
        arm_instances=True,
        instance_family=None,
        emr_version=None,
        mode="balanced",
    )
    assert result == mock_result


def test_optimize_invalid_parameters(facade):
    """Test that facade validation catches invalid parameters."""
    with pytest.raises(ValidationError):
        facade.optimize(cores=-1, memory=32)


def test_optimize_core_exception(facade, mock_engine, mock_core):
    """Test that facade correctly propagates exceptions from the core."""
    mock_core.optimize.side_effect = OptimizationError("Core failure")

    with pytest.raises(OptimizationError, match="Core failure"):
        facade.optimize(cores=8, memory=32)

    mock_engine.ensure_fresh_data.assert_called_once()


def test_cleanup(facade, mock_db):
    """Test cleanup disconnects the database."""
    # Enter context to initialize
    with facade:
        pass

    facade.cleanup()
    mock_db.disconnect.assert_called_once()
    assert not facade._initialized


def test_reset_instance_functionality():
    """Test that reset_instance properly cleans up and resets the singleton."""
    first_instance = SpotOptimizerFacade.get_instance()
    mock_cleanup = Mock()
    first_instance.cleanup = mock_cleanup

    SpotOptimizerFacade.reset_instance()
    mock_cleanup.assert_called_once()

    second_instance = SpotOptimizerFacade.get_instance()
    assert first_instance is not second_instance
    SpotOptimizerFacade.reset_instance()


def test_thread_safety_singleton():
    """Test that the singleton pattern is thread-safe."""
    SpotOptimizerFacade.reset_instance()
    instances = []

    def get_instance():
        instance = SpotOptimizerFacade.get_instance()
        instances.append(instance)

    threads = [threading.Thread(target=get_instance) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    first_instance = instances[0]
    for instance in instances[1:]:
        assert instance is first_instance

    SpotOptimizerFacade.reset_instance()

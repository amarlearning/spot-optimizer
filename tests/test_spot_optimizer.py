import pytest
from unittest.mock import Mock, patch

from spot_optimizer.spot_optimizer import SpotOptimizer
from spot_optimizer.optimizer_mode import Mode

@pytest.fixture
def mock_spot_advisor():
    advisor = Mock()
    advisor.fetch_data.return_value = {
        "instance_types": {
            "m6i.2xlarge": {
                "cores": 8,
                "memory": 32
            }
        }
    }
    return advisor

@pytest.fixture
def mock_db():
    db = Mock()
    db.connect = Mock()
    db.disconnect = Mock()
    return db

@pytest.fixture
def optimizer(mock_spot_advisor, mock_db):
    with patch('spot_optimizer.spot_optimizer.AwsSpotAdvisorData', return_value=mock_spot_advisor), \
         patch('spot_optimizer.spot_optimizer.DuckDBStorage', return_value=mock_db):
        optimizer = SpotOptimizer(db_path="test.db")
        yield optimizer

def test_singleton_pattern():
    """Test that get_instance returns the same instance."""
    first = SpotOptimizer.get_instance()
    second = SpotOptimizer.get_instance()
    assert first is second

def test_initialization(optimizer, mock_db):
    """Test optimizer initialization."""
    assert optimizer.db is mock_db
    mock_db.connect.assert_called_once()

def test_cleanup(optimizer, mock_db):
    """Test cleanup on deletion."""
    optimizer.__del__()
    mock_db.disconnect.assert_called_once()

def test_optimize_basic(optimizer):
    """Test basic optimization with minimal parameters."""
    result = optimizer.optimize(
        cores=8,
        memory=32
    )
    
    assert isinstance(result, dict)
    assert "instances" in result
    assert "type" in result["instances"]
    assert "count" in result["instances"]
    assert "mode" in result
    assert "total_cores" in result
    assert "total_ram" in result

def test_optimize_with_all_params(optimizer):
    """Test optimization with all parameters."""
    result = optimizer.optimize(
        cores=8,
        memory=32,
        region="us-east-1",
        ssd_only=True,
        arm_instances=False,
        instance_family=["m6i"],
        emr_version="6.9.0",
        mode=Mode.BALANCED.value
    )
    
    assert isinstance(result, dict)
    assert result["mode"] == "balanced"

@pytest.mark.parametrize("cores,memory", [
    (0, 32),  # Invalid cores
    (8, 0),   # Invalid memory
    (-1, 32), # Negative cores
    (8, -1),  # Negative memory
])
def test_optimize_invalid_params(optimizer, cores, memory):
    """Test optimization with invalid parameters."""
    with pytest.raises(ValueError):
        optimizer.optimize(cores=cores, memory=memory)

def test_optimize_handles_advisor_error(optimizer, mock_spot_advisor):
    """Test handling of advisor errors."""
    mock_spot_advisor.fetch_data.side_effect = Exception("Failed to fetch data")
    
    with pytest.raises(Exception) as exc_info:
        optimizer.optimize(cores=8, memory=32)
    assert "Failed to fetch data" in str(exc_info.value)

def test_optimize_mode_validation(optimizer):
    """Test mode parameter validation."""
    with pytest.raises(ValueError):
        optimizer.optimize(
            cores=8,
            memory=32,
            mode="invalid_mode"
        )

import os
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from spot_optimizer.spot_optimizer import SpotOptimizer
from spot_optimizer.optimizer_mode import Mode

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    with patch('spot_optimizer.spot_optimizer.user_data_dir') as mock_dir:
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
    with patch('spot_optimizer.spot_optimizer.DuckDBStorage') as mock_db_class, \
         patch('spot_optimizer.spot_optimizer.AwsSpotAdvisorData') as mock_advisor_class:
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
    SpotOptimizer._instance = None

def test_initialization(optimizer, mock_db):
    """Test optimizer initialization."""
    assert optimizer.db is mock_db
    mock_db.connect.assert_called_once()

def test_cleanup(mock_db, mock_advisor):
    """Test database cleanup on deletion."""
    optimizer = SpotOptimizer()
    optimizer.db = mock_db
    optimizer.__del__()
    mock_db.disconnect.assert_called_once()

@pytest.fixture
def sample_query_result():
    return pd.DataFrame({
        'instance_type': ['m5.xlarge'],
        'cores': [4],
        'ram_gb': [16],
        'spot_score': [75],
        'interruption_rate': [1],
        'instances_needed': [2],
        'total_cores': [8],
        'total_memory': [32],
        'cpu_waste_pct': [0],
        'memory_waste_pct': [0]
    })

def test_optimize_success(optimizer, mock_db, sample_query_result):
    """Test successful optimization with valid parameters."""
    mock_db.query_data.return_value = sample_query_result
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        region="us-west-2",
        ssd_only=False,
        arm_instances=True
    )
    
    assert result == {
        "instances": {
            "type": "m5.xlarge",
            "count": 2
        },
        "mode": "balanced",
        "total_cores": 8,
        "total_ram": 32,
        "reliability": {
            "spot_score": 75,
            "interruption_rate": 1
        }
    }

def test_optimize_no_results(optimizer, mock_db):
    """Test optimization when no suitable instances are found."""
    mock_db.query_data.return_value = pd.DataFrame()
    
    with pytest.raises(ValueError, match="No suitable instances found matching the requirements"):
        optimizer.optimize(cores=8, memory=32)

def test_optimize_with_instance_family(optimizer, mock_db, sample_query_result):
    """Test optimization with instance family filter."""
    mock_db.query_data.return_value = sample_query_result
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        instance_family=["m5", "c5"]
    )
    
    # Verify the result
    assert result["instances"]["type"] == "m5.xlarge"
    # Verify that the query included instance family filter
    query_call = mock_db.query_data.call_args[0][0]
    assert "instance_family IN" in query_call

def test_optimize_with_ssd_only(optimizer, mock_db, sample_query_result):
    """Test optimization with SSD-only filter."""
    mock_db.query_data.return_value = sample_query_result
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        ssd_only=True
    )
    
    # Verify the query included SSD filter
    query_call = mock_db.query_data.call_args[0][0]
    assert "storage_type = 'ssd'" in query_call

def test_optimize_with_arm_instances(optimizer, mock_db, sample_query_result):
    """Test optimization with ARM instances disabled."""
    mock_db.query_data.return_value = sample_query_result
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        arm_instances=False
    )
    
    # Verify the query excluded ARM instances
    query_call = mock_db.query_data.call_args[0][0]
    assert "architecture != 'arm64'" in query_call

@pytest.mark.parametrize("mode", [
    Mode.LATENCY.value,
    Mode.BALANCED.value,
    Mode.FAULT_TOLERANCE.value
])
def test_optimize_different_modes(optimizer, mock_db, sample_query_result, mode):
    """Test optimization with different modes."""
    mock_db.query_data.return_value = sample_query_result
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        mode=mode
    )
    
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

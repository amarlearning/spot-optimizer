import os
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from spot_optimizer.spot_optimizer import SpotOptimizer
from spot_optimizer.config import SpotOptimizerConfig
from spot_optimizer.optimizer_mode import Mode

@pytest.fixture
def mock_config(tmp_path):
    """Create a test configuration."""
    return SpotOptimizerConfig(
        db_path=str(tmp_path / "test.db"),
        cache_ttl=3600,
        request_timeout=30,
        max_retries=3
    )

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
def optimizer(mock_db, mock_advisor, mock_config):
    with patch('spot_optimizer.spot_optimizer.DuckDBStorage') as mock_db_class, \
         patch('spot_optimizer.spot_optimizer.AwsSpotAdvisorData') as mock_advisor_class, \
         patch('spot_optimizer.spot_optimizer.OptimizationQueryBuilder') as mock_query_builder_class:
        mock_db_class.return_value = mock_db
        mock_advisor_class.return_value = mock_advisor
        mock_query_builder = Mock()
        mock_query_builder_class.return_value = mock_query_builder
        optimizer = SpotOptimizer(mock_config)
        optimizer.query_builder = mock_query_builder
        yield optimizer
        
def test_default_db_path():
    """Test that default database path is created correctly."""
    db_path = SpotOptimizerConfig._get_default_db_path()
    assert db_path.endswith("spot_advisor_data.db")
    assert "spot-optimizer" in db_path

def test_singleton_pattern():
    """Test that SpotOptimizer follows singleton pattern."""
    first = SpotOptimizer.get_instance()
    second = SpotOptimizer.get_instance()
    assert first is second
    # Clean up singleton for other tests
    SpotOptimizer._instance = None

def test_initialization(optimizer, mock_db, mock_config):
    """Test optimizer initialization."""
    assert optimizer.db is mock_db
    assert optimizer.config is mock_config
    mock_db.connect.assert_called_once()

def test_cleanup(mock_db, mock_advisor, mock_config):
    """Test database cleanup on deletion."""
    with patch('spot_optimizer.spot_optimizer.DuckDBStorage') as mock_db_class, \
         patch('spot_optimizer.spot_optimizer.AwsSpotAdvisorData') as mock_advisor_class:
        mock_db_class.return_value = mock_db
        mock_advisor_class.return_value = mock_advisor
        optimizer = SpotOptimizer(mock_config)
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
    
    # Mock the query builder methods
    optimizer.query_builder.build_optimization_query.return_value = "SELECT * FROM instances"
    optimizer.query_builder.build_query_parameters.return_value = [8, 32, "us-west-2"]
    
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
    
    # Mock the error message builder to return expected string
    optimizer.query_builder.build_error_message_params.return_value = "No suitable instances found matching for cpu = 8 and memory = 32 and region = us-west-2 and mode = balanced"
    
    with pytest.raises(ValueError, match="No suitable instances found matching for cpu = 8 and memory = 32 and region = us-west-2 and mode = balanced"):
        optimizer.optimize(cores=8, memory=32)

def test_optimize_with_instance_family(optimizer, mock_db, sample_query_result):
    """Test optimization with instance family filter."""
    mock_db.query_data.return_value = sample_query_result
    
    # Mock the query builder to return a query string with instance family filter
    optimizer.query_builder.build_optimization_query.return_value = "SELECT * FROM instances WHERE instance_family IN (?, ?)"
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        instance_family=["m5", "c5"]
    )
    
    # Verify the result
    assert result["instances"]["type"] == "m5.xlarge"
    # Verify that the query builder was called with instance family
    optimizer.query_builder.build_optimization_query.assert_called_with(
        ssd_only=False,
        arm_instances=True,
        instance_family=["m5", "c5"]
    )

def test_optimize_with_ssd_only(optimizer, mock_db, sample_query_result):
    """Test optimization with SSD-only filter."""
    mock_db.query_data.return_value = sample_query_result
    
    # Mock the query builder to return a query string with SSD filter
    optimizer.query_builder.build_optimization_query.return_value = "SELECT * FROM instances WHERE storage_type = 'instance'"
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        ssd_only=True
    )
    
    # Verify that the query builder was called with ssd_only=True
    optimizer.query_builder.build_optimization_query.assert_called_with(
        ssd_only=True,
        arm_instances=True,
        instance_family=None
    )

def test_optimize_with_arm_instances(optimizer, mock_db, sample_query_result):
    """Test optimization with ARM instances disabled."""
    mock_db.query_data.return_value = sample_query_result
    
    # Mock the query builder to return a query string that excludes ARM
    optimizer.query_builder.build_optimization_query.return_value = "SELECT * FROM instances WHERE architecture != 'arm64'"
    
    result = optimizer.optimize(
        cores=8,
        memory=32,
        arm_instances=False
    )
    
    # Verify that the query builder was called with arm_instances=False
    optimizer.query_builder.build_optimization_query.assert_called_with(
        ssd_only=False,
        arm_instances=False,
        instance_family=None
    )

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

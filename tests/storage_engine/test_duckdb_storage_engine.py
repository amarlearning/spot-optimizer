import pytest
from spot_optimizer.storage_engine.duckdb_storage_engine import DuckDBStorage


@pytest.fixture
def sample_data():
    """Sample data fixture for testing."""
    return {
        "global_rate": "0.1",
        "instance_types": {
            "m5.xlarge": {
                "instance_family": "m5",
                "cores": 4,
                "ram_gb": 16.0,
                "storage_type": "EBS",
                "architecture": "x86_64",
                "network_performance": "Up to 10 Gigabit",
                "emr_compatible": True,
                "emr_min_version": "5.0.0"
            },
            "c6g.2xlarge": {
                "instance_family": "c6g",
                "cores": 8,
                "ram_gb": 16.0,
                "storage_type": "EBS",
                "architecture": "arm64",
                "network_performance": "Up to 12 Gigabit",
                "emr_compatible": True,
                "emr_min_version": "6.0.0"
            }
        },
        "ranges": [
            {"index": 1, "label": "low", "dots": 1, "max": 5},
            {"index": 2, "label": "medium", "dots": 2, "max": 10}
        ]
    }


@pytest.fixture
def db():
    """Create a new in-memory database for each test."""
    with DuckDBStorage(":memory:") as db:
        yield db


def test_connection_management(db):
    """Test database connection management."""
    assert db.conn is not None
    db.disconnect()
    assert db.conn is None
    db.connect()
    assert db.conn is not None


def test_store_and_query_data(db, sample_data):
    """Test storing and querying data."""
    db.store_data(sample_data)

    # Test querying global rate
    result = db.query_data("SELECT global_rate FROM global_rate")
    assert result['global_rate'].iloc[0] == "0.1"

    # Test querying instance types
    result = db.query_data("SELECT * FROM instance_types")
    assert len(result) == 2
    assert "m5.xlarge" in result['instance_type'].values
    assert "c6g.2xlarge" in result['instance_type'].values

    # Test querying ranges
    result = db.query_data("SELECT * FROM ranges")
    assert len(result) == 2
    assert result['label'].tolist() == ['low', 'medium']


def test_clear_data(db, sample_data):
    """Test clearing data from tables."""
    db.store_data(sample_data)
    db.clear_data()

    # Verify all tables are empty
    tables = ["cache_timestamp", "global_rate", "instance_types", "ranges", "spot_advisor"]
    for table in tables:
        result = db.query_data(f"SELECT COUNT(*) as count FROM {table}")
        assert result['count'].iloc[0] == 0


def test_query_with_parameters(db, sample_data):
    """Test querying with parameters."""
    db.store_data(sample_data)

    # Test query with single parameter
    result = db.query_data(
        "SELECT * FROM instance_types WHERE cores > ?",
        params=[4]
    )
    assert len(result) == 1
    assert result['instance_type'].iloc[0] == "c6g.2xlarge"

    # Test query with multiple parameters
    result = db.query_data(
        "SELECT * FROM instance_types WHERE cores > ? AND ram_gb = ?",
        params=[4, 16.0]
    )
    assert len(result) == 1
    assert result['instance_type'].iloc[0] == "c6g.2xlarge"


def test_error_handling(db):
    """Test error handling in database operations."""
    # Test invalid query
    with pytest.raises(RuntimeError) as exc_info:
        db.query_data("SELECT * FROM nonexistent_table")
    assert "Query failed" in str(exc_info.value)

    # Test storing invalid data
    with pytest.raises(RuntimeError) as exc_info:
        db.store_data({"invalid": "data"})
    assert "Failed to store data" in str(exc_info.value)


def test_context_manager():
    """Test using the storage engine as a context manager."""
    with DuckDBStorage(":memory:") as db:
        assert db.conn is not None
        db.query_data("SELECT 1")
    assert db.conn is None


def test_no_connection_operations():
    """Test operations without an active connection."""
    db = DuckDBStorage(":memory:")  # Don't use context manager
    
    with pytest.raises(RuntimeError) as exc_info:
        db.query_data("SELECT 1")
    assert "No database connection" in str(exc_info.value)

    with pytest.raises(RuntimeError) as exc_info:
        db.store_data({})
    assert "No database connection" in str(exc_info.value)

    with pytest.raises(RuntimeError) as exc_info:
        db.clear_data()
    assert "No database connection" in str(exc_info.value)

import pytest
from spot_optimizer.storage_engine.duckdb_storage_engine import DuckDBStorage
from spot_optimizer.exceptions import StorageError, ValidationError


@pytest.fixture
def sample_data():
    """Sample data for testing storage operations."""
    return {
        "global_rate": "0.1",
        "instance_types": {
            "m5.xlarge": {
                "cores": 4,
                "ram_gb": 16.0,
                "emr": True,
                "emr_min_version": "5.0.0",
            },
            "c6g.2xlarge": {
                "cores": 8,
                "ram_gb": 16.0,
                "emr": True,
                "emr_min_version": "6.0.0",
            },
        },
        "ranges": [
            {"index": 1, "label": "low", "dots": 1, "max": 5},
            {"index": 2, "label": "medium", "dots": 2, "max": 10},
        ],
        "spot_advisor": {
            "us-west-2": {
                "Linux": {
                    "m5.xlarge": {"s": 75, "r": 1},
                    "c6g.2xlarge": {"s": 65, "r": 2},
                },
                "Windows": {"m5.xlarge": {"s": 70, "r": 2}},
            },
            "us-east-1": {"Linux": {"m5.xlarge": {"s": 80, "r": 1}}},
        },
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
    assert result["global_rate"].iloc[0] == "0.1"

    # Test querying instance types
    result = db.query_data("SELECT * FROM instance_types")
    assert len(result) == 2
    assert "m5.xlarge" in result["instance_type"].values
    assert "c6g.2xlarge" in result["instance_type"].values

    # Test querying ranges
    result = db.query_data("SELECT * FROM ranges")
    assert len(result) == 2
    assert result["label"].tolist() == ["low", "medium"]


def test_clear_data(db, sample_data):
    """Test clearing data from tables."""
    db.store_data(sample_data)
    db.clear_data()

    # Verify all tables are empty
    tables = [
        "cache_timestamp",
        "global_rate",
        "instance_types",
        "ranges",
        "spot_advisor",
    ]
    for table in tables:
        result = db.query_data(f"SELECT COUNT(*) as count FROM {table}")
        assert result["count"].iloc[0] == 0


def test_query_with_parameters(db, sample_data):
    """Test querying with parameters."""
    db.store_data(sample_data)

    # Test query with single parameter
    result = db.query_data("SELECT * FROM instance_types WHERE cores > ?", params=[4])
    assert len(result) == 1
    assert result["instance_type"].iloc[0] == "c6g.2xlarge"

    # Test query with multiple parameters
    result = db.query_data(
        "SELECT * FROM instance_types WHERE cores > ? AND ram_gb = ?", params=[4, 16.0]
    )
    assert len(result) == 1
    assert result["instance_type"].iloc[0] == "c6g.2xlarge"


def test_error_handling(db):
    """Test error handling in database operations."""
    # Test invalid query
    with pytest.raises(StorageError, match="Database query failed"):
        db.query_data("SELECT * FROM nonexistent_table")

    # Test storing invalid data
    with pytest.raises(StorageError, match="Failed to store data in database"):
        db.store_data({"invalid": "data"})


def test_context_manager():
    """Test using the storage engine as a context manager."""
    with DuckDBStorage(":memory:") as db:
        assert db.conn is not None
        db.query_data("SELECT 1")
    assert db.conn is None


def test_no_connection_operations():
    """Test operations without an active connection."""
    db = DuckDBStorage(":memory:")  # Don't use context manager

    with pytest.raises(StorageError) as exc_info:
        db.query_data("SELECT 1")
    assert "No database connection" in str(exc_info.value)

    with pytest.raises(StorageError) as exc_info:
        db.store_data({})
    assert "No database connection" in str(exc_info.value)

    with pytest.raises(StorageError) as exc_info:
        db.clear_data()
    assert "No database connection" in str(exc_info.value)


def test_table_name_validation():
    """Test table name validation against whitelist."""
    db = DuckDBStorage(":memory:")

    # Valid table names should not raise an exception
    for table_name in db.VALID_TABLES:
        db._validate_table_name(table_name)  # Should not raise

    # Invalid table names should raise ValidationError
    invalid_tables = [
        "users; DROP TABLE instance_types; --",
        "' OR '1'='1",
        "nonexistent_table",
        "test_table",
        "malicious_table",
        "",
        "SELECT * FROM users",
        "instance_types; DELETE FROM ranges; --",
    ]

    for invalid_table in invalid_tables:
        with pytest.raises(ValidationError) as exc_info:
            db._validate_table_name(invalid_table)
        assert "Invalid table name" in str(exc_info.value)


def test_clear_data_sql_injection_prevention(db, sample_data):
    """Test that clear_data is protected against SQL injection."""
    # Store some data first
    db.store_data(sample_data)

    # Verify data exists
    result = db.query_data("SELECT COUNT(*) as count FROM instance_types")
    assert result["count"].iloc[0] > 0

    # Clear data using the secure method
    db.clear_data()

    # Verify all tables are empty
    tables = [
        "cache_timestamp",
        "global_rate",
        "instance_types",
        "ranges",
        "spot_advisor",
    ]
    for table in tables:
        result = db.query_data(f"SELECT COUNT(*) as count FROM {table}")
        assert result["count"].iloc[0] == 0


def test_valid_tables_constant():
    """Test that VALID_TABLES contains all expected table names."""
    db = DuckDBStorage(":memory:")

    expected_tables = {
        "cache_timestamp",
        "global_rate",
        "instance_types",
        "ranges",
        "spot_advisor",
    }

    assert db.VALID_TABLES == expected_tables
    assert len(db.VALID_TABLES) == 5


def test_backward_compatibility_clear_data(db, sample_data):
    """Test that the secure clear_data method maintains backward compatibility."""
    # Store sample data
    db.store_data(sample_data)

    # Verify data exists before clearing
    result = db.query_data("SELECT COUNT(*) as count FROM instance_types")
    assert result["count"].iloc[0] == 2

    result = db.query_data("SELECT COUNT(*) as count FROM ranges")
    assert result["count"].iloc[0] == 2

    # Clear data - this should work exactly as before
    db.clear_data()

    # Verify all tables are empty (same behavior as before)
    tables = [
        "cache_timestamp",
        "global_rate",
        "instance_types",
        "ranges",
        "spot_advisor",
    ]
    for table in tables:
        result = db.query_data(f"SELECT COUNT(*) as count FROM {table}")
        assert result["count"].iloc[0] == 0

import pytest
import pandas as pd

from datetime import datetime, timedelta
from unittest.mock import Mock

from spot_optimizer.spot_advisor_engine import (
    should_refresh_data,
    refresh_spot_data,
    ensure_fresh_data,
    CACHE_EXPIRY_SECONDS,
)


@pytest.fixture
def mock_db():
    """Mock database with required methods."""
    return Mock()


@pytest.fixture
def mock_advisor():
    """Mock spot advisor with required methods."""
    return Mock()


@pytest.fixture
def sample_spot_data():
    """Sample spot advisor data."""
    return {
        "global_rate": "0.1",
        "instance_types": {"m5.xlarge": {"cores": 4, "ram_gb": 16.0}},
        "ranges": [{"index": 1, "label": "low", "dots": 1, "max": 5}],
    }


def test_should_refresh_data_empty_db(mock_db):
    """Test should_refresh_data when database is empty."""
    mock_db.query_data.return_value = pd.DataFrame()

    assert should_refresh_data(mock_db) is True
    mock_db.query_data.assert_called_once()


def test_should_refresh_data_expired(mock_db):
    """Test should_refresh_data when cache is expired."""
    old_timestamp = datetime.now() - timedelta(seconds=CACHE_EXPIRY_SECONDS + 100)
    mock_db.query_data.return_value = pd.DataFrame({"timestamp": [old_timestamp]})

    assert should_refresh_data(mock_db) is True


def test_should_refresh_data_fresh(mock_db):
    """Test should_refresh_data when cache is fresh."""
    fresh_timestamp = datetime.now() - timedelta(seconds=CACHE_EXPIRY_SECONDS - 100)
    mock_db.query_data.return_value = pd.DataFrame({"timestamp": [fresh_timestamp]})

    assert should_refresh_data(mock_db) is False


def test_should_refresh_data_db_error(mock_db):
    """Test should_refresh_data handles database errors."""
    mock_db.query_data.side_effect = Exception("Database error")

    assert should_refresh_data(mock_db) is True


def test_refresh_spot_data(mock_advisor, mock_db, sample_spot_data):
    """Test refresh_spot_data functionality."""
    mock_advisor.fetch_data.return_value = sample_spot_data

    refresh_spot_data(mock_advisor, mock_db)

    mock_advisor.fetch_data.assert_called_once()
    mock_db.clear_data.assert_called_once()
    mock_db.store_data.assert_called_once_with(sample_spot_data)


def test_refresh_spot_data_error(mock_advisor, mock_db):
    """Test refresh_spot_data error handling."""
    mock_advisor.fetch_data.side_effect = Exception("Fetch error")

    with pytest.raises(Exception, match="Fetch error"):
        refresh_spot_data(mock_advisor, mock_db)


def test_ensure_fresh_data_when_needed(mock_advisor, mock_db, sample_spot_data):
    """Test ensure_fresh_data when refresh is needed."""
    mock_db.query_data.return_value = pd.DataFrame()  # Empty DB
    mock_advisor.fetch_data.return_value = sample_spot_data

    ensure_fresh_data(mock_advisor, mock_db)

    mock_advisor.fetch_data.assert_called_once()
    mock_db.clear_data.assert_called_once()
    mock_db.store_data.assert_called_once_with(sample_spot_data)


def test_ensure_fresh_data_when_not_needed(mock_advisor, mock_db):
    """Test ensure_fresh_data when refresh is not needed."""
    fresh_timestamp = datetime.now() - timedelta(seconds=CACHE_EXPIRY_SECONDS - 100)
    mock_db.query_data.return_value = pd.DataFrame({"timestamp": [fresh_timestamp]})

    ensure_fresh_data(mock_advisor, mock_db)

    mock_advisor.fetch_data.assert_not_called()
    mock_db.clear_data.assert_not_called()
    mock_db.store_data.assert_not_called()


def test_ensure_fresh_data_error_handling(mock_advisor, mock_db):
    """Test ensure_fresh_data error handling."""
    mock_db.query_data.side_effect = Exception("Database error")
    mock_advisor.fetch_data.side_effect = Exception("Fetch error")

    with pytest.raises(Exception, match="Fetch error"):
        ensure_fresh_data(mock_advisor, mock_db)


def test_ensure_fresh_data_error_handling(mock_advisor, mock_db):
    """Test ensure_fresh_data error handling."""
    mock_db.query_data.side_effect = Exception("Database error")
    mock_advisor.fetch_data.side_effect = Exception("Fetch error")

    # DB error is treated as cache miss, so it will try to fetch,
    # which will then fail with Fetch error
    with pytest.raises(Exception, match="Fetch error"):
        ensure_fresh_data(mock_advisor, mock_db)

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pandas as pd

from spot_optimizer.spot_advisor_engine import SpotAdvisorEngine, CACHE_EXPIRY_SECONDS
from spot_optimizer.exceptions import (
    StorageError,
    DataError,
    NetworkError,
    ErrorCode,
)

@pytest.fixture
def mock_advisor():
    """Fixture for a mocked AWS Spot Advisor."""
    return Mock()

@pytest.fixture
def mock_db():
    """Fixture for a mocked database."""
    db = Mock()
    db.query_data = Mock()
    db.clear_data = Mock()
    db.store_data = Mock()
    return db

@pytest.fixture
def engine(mock_advisor, mock_db):
    """Fixture for SpotAdvisorEngine with mocked dependencies."""
    return SpotAdvisorEngine(advisor=mock_advisor, db=mock_db)

def test_should_refresh_data_empty_timestamp(engine, mock_db):
    """Test that data should be refreshed if no timestamp is found."""
    mock_db.query_data.return_value = pd.DataFrame()
    assert engine.should_refresh_data() is True

def test_should_refresh_data_expired_cache(engine, mock_db):
    """Test that data should be refreshed if the cache is expired."""
    expired_time = datetime.now() - timedelta(seconds=CACHE_EXPIRY_SECONDS + 1)
    mock_db.query_data.return_value = pd.DataFrame({"timestamp": [expired_time]})
    assert engine.should_refresh_data() is True

def test_should_not_refresh_data_fresh_cache(engine, mock_db):
    """Test that data should not be refreshed if the cache is fresh."""
    fresh_time = datetime.now() - timedelta(seconds=CACHE_EXPIRY_SECONDS - 1)
    mock_db.query_data.return_value = pd.DataFrame({"timestamp": [fresh_time]})
    assert engine.should_refresh_data() is False

def test_should_refresh_on_storage_error(engine, mock_db):
    """Test that data should be refreshed if a storage error occurs."""
    mock_db.query_data.side_effect = StorageError("DB connection failed")
    assert engine.should_refresh_data() is True

def test_refresh_spot_data_success(engine, mock_advisor, mock_db):
    """Test successful data refresh."""
    mock_data = {"regions": {}}
    mock_advisor.fetch_data.return_value = mock_data
    engine.refresh_spot_data()
    mock_advisor.fetch_data.assert_called_once()
    mock_db.clear_data.assert_called_once()
    mock_db.store_data.assert_called_once_with(mock_data)

@pytest.mark.parametrize(
    "exception_type", [NetworkError, StorageError, DataError]
)
def test_refresh_spot_data_propagates_known_errors(
    engine, mock_advisor, exception_type
):
    """Test that known errors are propagated during data refresh."""
    mock_advisor.fetch_data.side_effect = exception_type("Test Error")
    with pytest.raises(exception_type):
        engine.refresh_spot_data()

def test_refresh_spot_data_unexpected_error(engine, mock_advisor):
    """Test that unexpected errors are wrapped in DataError."""
    mock_advisor.fetch_data.side_effect = Exception("Unexpected failure")
    with pytest.raises(DataError) as exc_info:
        engine.refresh_spot_data()
    assert exc_info.value.error_code == ErrorCode.DATA_REFRESH_FAILED

@patch("spot_optimizer.spot_advisor_engine.SpotAdvisorEngine.should_refresh_data")
@patch("spot_optimizer.spot_advisor_engine.SpotAdvisorEngine.refresh_spot_data")
def test_ensure_fresh_data_refreshes_when_needed(
    mock_refresh, mock_should_refresh, engine
):
    """Test that fresh data is ensured when refresh is needed."""
    mock_should_refresh.return_value = True
    engine.ensure_fresh_data()
    mock_refresh.assert_called_once()

@patch("spot_optimizer.spot_advisor_engine.SpotAdvisorEngine.should_refresh_data")
@patch("spot_optimizer.spot_advisor_engine.SpotAdvisorEngine.refresh_spot_data")
def test_ensure_fresh_data_does_not_refresh_when_not_needed(
    mock_refresh, mock_should_refresh, engine
):
    """Test that fresh data is not refreshed when not needed."""
    mock_should_refresh.return_value = False
    engine.ensure_fresh_data()
    mock_refresh.assert_not_called()

@patch("spot_optimizer.spot_advisor_engine.SpotAdvisorEngine.should_refresh_data")
def test_ensure_fresh_data_unexpected_error(mock_should_refresh, engine):
    """Test that unexpected errors in ensure_fresh_data are wrapped."""
    mock_should_refresh.side_effect = Exception("Chaos")
    with pytest.raises(DataError) as exc_info:
        engine.ensure_fresh_data()
    assert exc_info.value.error_code == ErrorCode.DATA_REFRESH_FAILED

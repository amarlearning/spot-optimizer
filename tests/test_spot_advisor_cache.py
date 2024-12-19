import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from spark_cluster_optimiser.spot_advisor_cache import (
    clear_cache,
    get_spot_advisor_json,
)


@pytest.fixture
def mock_cache():
    with patch(
        "spark_cluster_optimiser.spot_advisor_cache.cache", autospec=True
    ) as mock_cache:
        yield mock_cache


@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        yield mock_get


def test_get_spot_advisor_json_cached(mock_cache):
    mock_cache.get.return_value = {
        "data": {"key": "value"},
        "timestamp": time.time(),
    }
    result = get_spot_advisor_json()

    assert result == {"key": "value"}
    mock_cache.get.assert_called_once_with("spot_advisor_json", default=None)


def test_clear_cache(mock_cache):
    clear_cache()
    mock_cache.clear.assert_called_once()


def test_get_spot_advisor_json_not_cached(mock_cache, mock_requests_get):
    mock_cache.get.return_value = None
    mock_requests_get.return_value = MagicMock(
        status_code=200, json=lambda: {"key": "value"}
    )

    result = get_spot_advisor_json()

    assert result == {"key": "value"}
    mock_cache.set.assert_called_once()
    mock_requests_get.assert_called_once_with(
        "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
    )


def test_get_spot_advisor_json_expired_cache(mock_cache, mock_requests_get):
    mock_cache.get.return_value = {
        "data": {"key": "value"},
        "timestamp": time.time() - 7200,  # 2 hours ago
    }
    mock_requests_get.return_value = MagicMock(
        status_code=200, json=lambda: {"key": "new_value"}
    )

    result = get_spot_advisor_json()

    assert result == {"key": "new_value"}
    mock_cache.set.assert_called_once()
    mock_requests_get.assert_called_once_with(
        "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
    )


def test_get_spot_advisor_json_fetch_failure(mock_cache, mock_requests_get):
    mock_cache.get.return_value = None
    mock_requests_get.return_value = MagicMock(status_code=400)

    data = get_spot_advisor_json()

    assert data is None
    mock_cache.set.assert_not_called()
    mock_requests_get.assert_called_once_with(
        "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
    )

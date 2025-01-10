import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from spark_cluster_optimiser.spot_advisor_data.aws_spot_advisor_cache import (
    AwsSpotAdvisorData,
)

SAMPLE_SPOT_ADVISOR_DATA = {
    "global_rate": "<10%",
    "instance_types": {
        "i4i.12xlarge": {"emr": True, "cores": 48, "ram_gb": 384.0}
    },
    "ranges": [{"index": 0, "label": "<5%", "dots": 0, "max": 5}],
    "spot_advisor": {
        "ap-southeast-4": {"Linux": {"i4i.12xlarge": {"s": 70, "r": 4}}}
    },
}


@pytest.fixture
def mock_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_SPOT_ADVISOR_DATA
    return mock_resp


@patch("requests.get")
def test_fetch_from_source_success(mock_get, mock_response):
    mock_get.return_value = mock_response
    advisor = AwsSpotAdvisorData()
    data = advisor._fetch_from_source()
    assert data == SAMPLE_SPOT_ADVISOR_DATA


@patch("requests.get")
def test_fetch_from_source_failure(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    mock_get.return_value = mock_resp
    advisor = AwsSpotAdvisorData()
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        advisor._fetch_from_source()

    assert (
        str(excinfo.value)
        == "Received status code 404 from https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
    )


@patch("requests.get")
def test_fetch_data_with_cache(mock_get, mock_response):
    mock_get.return_value = mock_response
    advisor = AwsSpotAdvisorData()
    advisor.cache = {"cached": "data"}
    advisor.last_fetch_time = time.time()
    data = advisor.fetch_data()
    assert data == {"cached": "data"}


@patch("requests.get")
def test_fetch_data_without_cache(mock_get, mock_response):
    mock_get.return_value = mock_response
    advisor = AwsSpotAdvisorData()
    advisor.cache = None
    advisor.last_fetch_time = 0
    data = advisor.fetch_data()
    assert data == SAMPLE_SPOT_ADVISOR_DATA
    assert advisor.cache == SAMPLE_SPOT_ADVISOR_DATA
    assert advisor.last_fetch_time > 0


@patch("requests.get")
def test_fetch_data_cache_expired(mock_get, mock_response):
    mock_get.return_value = mock_response
    advisor = AwsSpotAdvisorData()
    advisor.cache = {"cached": "data"}
    advisor.last_fetch_time = time.time() - 4000  # Cache expired
    data = advisor.fetch_data()
    assert data == SAMPLE_SPOT_ADVISOR_DATA
    assert advisor.cache == SAMPLE_SPOT_ADVISOR_DATA
    assert advisor.last_fetch_time > 0

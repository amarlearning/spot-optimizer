import pytest
import requests
from unittest.mock import patch, Mock

from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.exceptions import ValidationError, NetworkError, DataError


@pytest.fixture
def sample_spot_data():
    """Sample spot advisor response data."""
    return {
        "global_rate": "0.1",
        "instance_types": {"m5.xlarge": {"cores": 4, "ram_gb": 16.0}},
        "ranges": [{"index": 1, "label": "low", "dots": 1, "max": 5}],
    }


def test_init_with_valid_url():
    """Test initialization with valid URL."""
    advisor = AwsSpotAdvisorData(
        url="https://example.com/data.json", request_timeout=20, max_retries=2
    )
    assert advisor.url == "https://example.com/data.json"
    assert advisor.request_timeout == 20
    assert advisor.max_retries == 2


@pytest.mark.parametrize(
    "invalid_url",
    [
        "",  # Empty
        "not_a_url",  # No scheme
        "http://",  # No netloc
        "://example.com",  # No scheme
    ],
)
def test_init_with_invalid_url(invalid_url):
    """Test initialization with invalid URLs."""
    with pytest.raises(ValidationError, match="Invalid URL"):
        AwsSpotAdvisorData(url=invalid_url)


@patch("requests.get")
def test_fetch_data_success(mock_get, sample_spot_data):
    """Test successful data fetch."""
    mock_response = Mock()
    mock_response.json.return_value = sample_spot_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    advisor = AwsSpotAdvisorData()
    data = advisor.fetch_data()

    assert data == sample_spot_data
    mock_get.assert_called_once_with(advisor.url, timeout=advisor.request_timeout)


@patch("requests.get")
def test_fetch_data_retry_success(mock_get, sample_spot_data):
    """Test successful fetch after retries."""
    # First call fails, second succeeds
    mock_fail = Mock()
    mock_fail.raise_for_status.side_effect = requests.RequestException("Failed")

    mock_success = Mock()
    mock_success.json.return_value = sample_spot_data
    mock_success.raise_for_status.return_value = None

    mock_get.side_effect = [mock_fail, mock_success]

    advisor = AwsSpotAdvisorData(max_retries=2)
    data = advisor.fetch_data()

    assert data == sample_spot_data
    assert mock_get.call_count == 2


@patch("requests.get")
def test_fetch_data_all_retries_fail(mock_get):
    """Test when all retry attempts fail."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.RequestException("Failed")
    mock_get.return_value = mock_response

    advisor = AwsSpotAdvisorData(max_retries=2)

    with pytest.raises(NetworkError) as exc_info:
        advisor.fetch_data()

    assert "Failed to fetch data after 2 attempts" in str(exc_info.value)
    assert mock_get.call_count == 2


@patch("requests.get")
def test_fetch_data_invalid_json(mock_get):
    """Test handling of invalid JSON response."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.headers = {}
    mock_response.text = "invalid json"
    mock_get.return_value = mock_response

    advisor = AwsSpotAdvisorData()

    with pytest.raises(DataError):
        advisor.fetch_data()


@patch("requests.get")
def test_fetch_data_timeout(mock_get):
    """Test handling of request timeout."""
    mock_get.side_effect = requests.Timeout("Request timed out")

    advisor = AwsSpotAdvisorData(request_timeout=1)

    with pytest.raises(NetworkError):
        advisor.fetch_data()

    assert mock_get.call_count == advisor.max_retries


@patch("time.sleep")
@patch("requests.get")
def test_exponential_backoff(mock_get, mock_sleep):
    """Test exponential backoff between retries."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.RequestException("Failed")
    mock_get.return_value = mock_response

    advisor = AwsSpotAdvisorData(max_retries=3)

    with pytest.raises(NetworkError):
        advisor.fetch_data()

    # Should have tried to sleep twice (not on last attempt)
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1)  # 2^0
    mock_sleep.assert_any_call(2)  # 2^1

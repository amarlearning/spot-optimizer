import time
from urllib.parse import urlparse, ParseResult
from typing import Dict, Any

import requests
from requests.exceptions import RequestException
from spot_optimizer.logging_config import get_logger
from spot_optimizer.exceptions import (
    ValidationError,
    ErrorCode,
    NetworkError,
    DataError,
)

logger = get_logger(__name__)


class AwsSpotAdvisorData:
    """Fetches AWS Spot Advisor data."""

    def __init__(
        self,
        url: str = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json",
        request_timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """Initialize the AWS Spot Advisor data fetcher.
        :param url: The URL to fetch JSON data from.
        :param request_timeout: Timeout for HTTP requests in seconds.
        :param max_retries: Maximum number of retry attempts for failed requests.
        """
        self._validate_url(url)
        self.url: str = url
        self.request_timeout: int = request_timeout
        self.max_retries: int = max_retries

    @staticmethod
    def _validate_url(url: str) -> None:
        """Validate the URL format."""
        try:
            result: ParseResult = urlparse(url)
            if not all([result.scheme, result.netloc]) or result.scheme not in [
                "http",
                "https",
            ]:
                raise ValidationError(
                    "Invalid URL format",
                    error_code=ErrorCode.INVALID_URL,
                    context={"url": url},
                )
        except Exception as e:
            raise ValidationError(
                f"Invalid URL: {e}",
                error_code=ErrorCode.INVALID_URL,
                context={"url": url},
                cause=e,
            )

    def fetch_data(self) -> Dict[str, Any]:
        """Fetch the Spot Advisor data from AWS.
        :return: The fetched data.
        :raises NetworkError: If the request fails after all retries.
        :raises DataError: If JSON parsing fails.
        """
        last_exception: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.url, timeout=self.request_timeout)
                response.raise_for_status()
                return response.json()
            except ValueError as e:
                raise DataError(
                    f"Failed to parse JSON response: {e}",
                    error_code=ErrorCode.DATA_INVALID_FORMAT,
                    cause=e,
                )
            except RequestException as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)

        raise NetworkError(
            f"Failed to fetch data after {self.max_retries} attempts",
            error_code=ErrorCode.NETWORK_REQUEST_FAILED,
            cause=last_exception,
        )

import time
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException
from spot_optimizer.logging_config import get_logger
from spot_optimizer.exceptions import (
    ValidationError,
    ErrorCode,
    raise_validation_error,
    raise_network_error,
    raise_data_error,
)

logger = get_logger(__name__)


class AwsSpotAdvisorData:
    """Fetches AWS Spot Advisor data."""

    def __init__(
        self,
        url: str = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json",
        request_timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize the AWS Spot Advisor data fetcher.

        Args:
            url: The URL to fetch JSON data from.
            request_timeout: Timeout for HTTP requests in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
        """
        self._validate_url(url)
        self.url = url
        self.request_timeout = request_timeout
        self.max_retries = max_retries

    @staticmethod
    def _validate_url(url: str) -> None:
        """Validate the URL format."""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise_validation_error(
                    "Invalid URL format - missing scheme or netloc",
                    error_code=ErrorCode.VALIDATION_INVALID_URL,
                    validation_context={"url": url, "parsed_result": str(result)},
                    suggestions=[
                        "Ensure URL starts with http:// or https://",
                        "Check that domain name is properly formatted",
                        "Verify URL is complete and valid",
                    ],
                )
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            raise_validation_error(
                f"Invalid URL: {str(e)}",
                error_code=ErrorCode.VALIDATION_INVALID_URL,
                validation_context={"url": url, "error": str(e)},
                suggestions=[
                    "Check URL format and syntax",
                    "Ensure URL is a valid string",
                    "Verify URL contains all required components",
                ],
                cause=e,
            )

    def fetch_data(self) -> dict:
        """
        Fetch the Spot Advisor data from AWS.

        Returns:
            dict: The fetched data.

        Raises:
            NetworkError: If the request fails after all retries.
            DataError: If JSON parsing fails.
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.url, timeout=self.request_timeout)
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError as e:
                    # JSON parsing error - this is a data error, not a network error
                    raise_data_error(
                        f"Failed to parse JSON response: {str(e)}",
                        error_code=ErrorCode.DATA_INVALID_FORMAT,
                        data_context={
                            "url": self.url,
                            "response_status": response.status_code,
                            "response_headers": dict(response.headers),
                            "response_text_preview": (
                                response.text[:500]
                                if hasattr(response, "text")
                                else "N/A"
                            ),
                        },
                        suggestions=[
                            "Check if AWS Spot Advisor API is returning valid JSON",
                            "Verify the URL is correct and points to JSON data",
                            "Check if the service is temporarily unavailable",
                            "Try again later as this might be a temporary issue",
                        ],
                        cause=e,
                    )
            except RequestException as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff

        message = f"Failed to fetch data after {self.max_retries} attempts"
        logger.error(message, exc_info=last_exception)
        raise_network_error(
            message=message,
            error_code=ErrorCode.NETWORK_REQUEST_FAILED,
            network_context={
                "url": self.url,
                "max_retries": self.max_retries,
                "request_timeout": self.request_timeout,
                "last_exception": str(last_exception) if last_exception else "Unknown",
            },
            suggestions=[
                "Check internet connectivity",
                "Verify AWS Spot Advisor service is accessible",
                "Check if firewall or proxy is blocking the request",
                "Try increasing request timeout if network is slow",
                "Check if AWS service is experiencing outages",
            ],
            cause=last_exception,
        )

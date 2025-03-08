import logging
import time
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

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
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

    def fetch_data(self) -> dict:
        """
        Fetch the Spot Advisor data from AWS.
        
        Returns:
            dict: The fetched data.
            
        Raises:
            RequestException: If the request fails after all retries or if JSON parsing fails.
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.url,
                    timeout=self.request_timeout
                )
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError as e:
                    raise RequestException(f"Failed to parse JSON response: {str(e)}") from e
            except RequestException as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                
        message = f"Failed to fetch data after {self.max_retries} attempts"
        logger.error(message, exc_info=last_exception)
        raise RequestException(message) from last_exception

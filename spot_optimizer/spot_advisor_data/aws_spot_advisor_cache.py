import logging
import time

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

CACHE_EXPIRY_DEFAULT = 3600  # 1 hour


class AwsSpotAdvisorData:
    def __init__(
        self,
        url: str = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json",
        cache_expiry: int = CACHE_EXPIRY_DEFAULT,
    ):
        """
        :param url: The URL to fetch JSON data from.
        :param cache_expiry: Cache expiry time in seconds (default: 1 hour).
        """
        self.cache = None
        self.last_fetch_time = 0
        self.cache_expiry = cache_expiry
        self.url = url

    def _fetch_from_source(self) -> dict:
        """
        Fetch the Spot Advisor JSON data from the URL.
        """
        response = requests.get(self.url)
        if response.status_code != 200:
            message = (
                f"Received status code {response.status_code} from {self.url}"
            )
            logger.error(
                message,
                extra={"response": response.text},
            )
            raise requests.exceptions.HTTPError(
                message,
                response=response,
            )
        return response.json()

    def fetch_data(self) -> dict:
        """
        Fetches data from the cache if valid, otherwise fetches fresh data.
        """
        current_time = time.time()
        if (
            self.cache is None
            or (current_time - self.last_fetch_time) > self.cache_expiry
        ):
            logger.info("Fetching fresh data...")
            self.cache = self._fetch_from_source()
            self.last_fetch_time = current_time
        else:
            logger.info("Using cached data.")
        return self.cache

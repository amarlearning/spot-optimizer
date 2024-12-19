import logging
import time

import diskcache as dc
import requests
from appdirs import user_cache_dir

CACHE_EXPIRATION = 3600  # 1 hour
SPOT_ADVISOR_URL = (
    "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
)

cache_dir = user_cache_dir(appname="spark-cluster-optimiser")
cache = dc.Cache(cache_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_spot_advisor_json():
    """Fetch the Spot Advisor JSON data from the URL."""
    response = requests.get(SPOT_ADVISOR_URL)
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(
            f"Received status code {response.status_code} from {SPOT_ADVISOR_URL}"
        )
    return response.json()


def get_spot_advisor_json():
    """Get the Spot Advisor JSON data, either from cache or by fetching it."""
    cached_data = cache.get("spot_advisor_json", default=None)

    if (
        cached_data is not None
        and time.time() - cached_data["timestamp"] < CACHE_EXPIRATION
    ):
        logger.info("Cache hit: Returning cached data.")
        return cached_data["data"]
    else:
        logger.info("Cache miss: Fetching new data.")
        clear_cache()
        try:
            data = fetch_spot_advisor_json()
            cache.set(
                "spot_advisor_json",
                {"data": data, "timestamp": time.time()},
                expire=CACHE_EXPIRATION,
            )
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Spot Advisor JSON data: {e}")
            return None


def clear_cache():
    """Clear the cache."""
    logger.info("Clearing cache.")
    cache.clear()

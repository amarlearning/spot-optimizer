import time

import diskcache as dc
import requests
from appdirs import user_cache_dir

cache_dir = user_cache_dir(appname="spark-cluster-optimiser")
cache = dc.Cache(cache_dir)


def fetch_spot_advisor_json():
    url = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
    response = requests.get(url)

    if response.status_code != 200:
        raise requests.exceptions.HTTPError(
            f"Received status code {response.status_code} from {url}"
        )

    return response.json()


def get_spot_advisor_json():
    cached_data = cache.get("spot_advisor_json", default=None)

    if (
        cached_data is not None
        and time.time() - cached_data["timestamp"] < 3600
    ):
        return cached_data["data"]
    else:
        clear_cache()
        data = fetch_spot_advisor_json()
        cache.set(
            "spot_advisor_json",
            {"data": data, "timestamp": time.time()},
            expire=3600,
        )
        return data


def clear_cache():
    cache.clear()

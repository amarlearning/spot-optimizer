import logging
from datetime import datetime

import pandas as pd

from spark_cluster_optimiser.spot_advisor_data.aws_spot_advisor_cache import (
    AwsSpotAdvisorData,
)
from spark_cluster_optimiser.storage_engine.storage_engine import StorageEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

CACHE_EXPIRY_DEFAULT = 3600  # 1 hour


def fetch_and_store_spot_data(
    advisor: AwsSpotAdvisorData, db: StorageEngine
) -> None:
    """
    Fetch Spot Advisor data if not already present or outdated, and store it in DuckDB.
    """
    try:
        query = "SELECT timestamp AS last_update FROM cache_timestamp"
        result = db.query_data(query)

        if not result.empty and result.iloc[0]["last_update"]:
            last_update = pd.Timestamp(result.iloc[0]["last_update"])
            if (
                datetime.now() - last_update
            ).total_seconds() < CACHE_EXPIRY_DEFAULT:
                logger.info("Data in storage is up-to-date. Skipping fetch.")
                print("Data in storage is up-to-date. Skipping fetch.")
                return

        logger.info("Fetching fresh data from Spot Advisor...")
        print("Fetching fresh data from Spot Advisor...")
        db.clear_data()
        db.store_data(advisor.fetch_data())
    except Exception as e:
        print(f"Error fetching and storing data: {e}")
        logger.error(f"Error fetching and storing data: {e}")
        raise

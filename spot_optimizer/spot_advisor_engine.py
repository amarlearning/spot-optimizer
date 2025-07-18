from datetime import datetime
import pandas as pd
from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.storage_engine.storage_engine import StorageEngine
from spot_optimizer.logging_config import get_logger
from spot_optimizer.exceptions import (
    StorageError,
    DataError,
    NetworkError,
    ErrorCode,
    raise_storage_error,
    raise_data_error,
)


logger = get_logger(__name__)


CACHE_EXPIRY_SECONDS: int = 3600


class SpotAdvisorEngine:
    """Manages the lifecycle of spot advisor data."""

    def __init__(self, advisor: AwsSpotAdvisorData, db: StorageEngine):
        """
        Initialize the engine with its dependencies.
        Args:
            advisor: Spot advisor data fetcher.
            db: Database storage engine.
        """
        self.advisor = advisor
        self.db = db

    def should_refresh_data(self) -> bool:
        """Check if the data needs to be refreshed."""
        try:
            result: pd.DataFrame = self.db.query_data(
                "SELECT timestamp FROM cache_timestamp ORDER BY timestamp DESC LIMIT 1"
            )
            if result.empty:
                return True

            last_update: datetime = result.iloc[0]["timestamp"]
            time_since_update: float = (datetime.now() - last_update).total_seconds()

            logger.info(f"Time since last update: {time_since_update} seconds")
            return time_since_update > CACHE_EXPIRY_SECONDS
        except StorageError as e:
            logger.warning(f"Storage error checking cache timestamp: {e}")
            return True  # Default to refresh
        except (KeyError, IndexError, TypeError) as e:
            logger.warning(f"Data format error checking cache timestamp: {e}")
            raise_data_error(
                "Invalid cache timestamp data format",
                error_code=ErrorCode.DATA_INVALID_FORMAT,
                cause=e,
            )
        except Exception as e:
            logger.warning(f"Unexpected error checking cache timestamp: {e}")
            raise_storage_error(
                message="Unexpected error checking cache timestamp",
                error_code=ErrorCode.STORAGE_QUERY_FAILED,
                cause=e,
            )

    def refresh_spot_data(self) -> None:
        """Fetch fresh data and store it in the database."""
        try:
            logger.info("Fetching fresh spot advisor data...")
            data = self.advisor.fetch_data()
            self.db.clear_data()
            self.db.store_data(data)
            logger.info("Spot advisor data updated successfully")
        except (NetworkError, StorageError, DataError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error refreshing spot data: {e}")
            raise_data_error(
                "Unexpected error refreshing spot advisor data",
                error_code=ErrorCode.DATA_REFRESH_FAILED,
                cause=e,
            )

    def ensure_fresh_data(self) -> None:
        """Ensure the database has fresh spot advisor data."""
        try:
            if self.should_refresh_data():
                self.refresh_spot_data()
            else:
                logger.info("Using existing spot advisor data from database")
        except (NetworkError, StorageError, DataError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error ensuring fresh data: {e}")
            raise_data_error(
                "Unexpected error ensuring fresh spot advisor data",
                error_code=ErrorCode.DATA_REFRESH_FAILED,
                cause=e,
            )

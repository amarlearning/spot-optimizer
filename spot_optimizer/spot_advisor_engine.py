from datetime import datetime

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


def should_refresh_data(db: StorageEngine) -> bool:
    """
    Check if the data needs to be refreshed.

    Args:
        db: Database connection

    Returns:
        bool: True if data should be refreshed
    """
    try:
        result: pd.DataFrame = db.query_data(
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
        return True  # Default to refresh if we can't check timestamp
    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Data format error checking cache timestamp: {e}")
        # Convert to DataError for consistency
        raise_data_error(
            "Invalid cache timestamp data format",
            error_code=ErrorCode.DATA_INVALID_FORMAT,
            data_context={
                "query_result": str(result) if "result" in locals() else "N/A"
            },
            suggestions=[
                "Check if cache_timestamp table has correct schema",
                "Verify timestamp column exists and has correct data type",
                "Consider clearing cache and refreshing data",
            ],
            cause=e,
        )
    except Exception as e:
        logger.warning(f"Unexpected error checking cache timestamp: {e}")
        # Convert to StorageError for consistency
        raise_storage_error(
            message="Unexpected error checking cache timestamp",
            error_code=ErrorCode.STORAGE_QUERY_FAILED,
            storage_context={"operation": "check_cache_timestamp"},
            suggestions=[
                "Check database connection",
                "Verify cache_timestamp table exists",
                "Check database permissions",
            ],
            cause=e,
        )


def refresh_spot_data(advisor: AwsSpotAdvisorData, db: StorageEngine) -> None:
    """
    Fetch fresh data and store in database.

    Args:
        advisor: Spot advisor data fetcher
        db: Database connection
    """
    try:
        logger.info("Fetching fresh spot advisor data...")
        data = advisor.fetch_data()

        # Clear existing data
        db.clear_data()

        # Store new data
        db.store_data(data)
        logger.info("Spot advisor data updated successfully")
    except NetworkError:
        # Re-raise network errors as-is - they already have proper context
        raise
    except StorageError:
        # Re-raise storage errors as-is - they already have proper context
        raise
    except DataError:
        # Re-raise data errors as-is - they already have proper context
        raise
    except Exception as e:
        logger.error(f"Unexpected error refreshing spot data: {e}")
        # Wrap unexpected errors in DataError
        raise_data_error(
            "Unexpected error refreshing spot advisor data",
            error_code=ErrorCode.DATA_REFRESH_FAILED,
            data_context={"advisor_type": type(advisor).__name__},
            suggestions=[
                "Check network connectivity",
                "Verify AWS Spot Advisor service is accessible",
                "Check database connection and permissions",
                "Try again later if this is a temporary issue",
            ],
            cause=e,
        )


def ensure_fresh_data(advisor: AwsSpotAdvisorData, db: StorageEngine) -> None:
    """
    Ensure the database has fresh spot advisor data.

    Args:
        advisor: Spot advisor data fetcher
        db: Database connection
    """
    try:
        if should_refresh_data(db):
            refresh_spot_data(advisor, db)
        else:
            logger.info("Using existing spot advisor data from database")
    except (NetworkError, StorageError, DataError):
        # Re-raise custom exceptions as-is - they already have proper context
        raise
    except Exception as e:
        logger.error(f"Unexpected error ensuring fresh data: {e}")
        # Wrap unexpected errors in DataError
        raise_data_error(
            "Unexpected error ensuring fresh spot advisor data",
            error_code=ErrorCode.DATA_REFRESH_FAILED,
            data_context={
                "advisor_type": type(advisor).__name__,
                "storage_type": type(db).__name__,
            },
            suggestions=[
                "Check network connectivity to AWS Spot Advisor service",
                "Verify database connection and permissions",
                "Check system resources and disk space",
                "Try again later if this is a temporary issue",
            ],
            cause=e,
        )

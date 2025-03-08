import logging
from datetime import datetime, timedelta

from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.storage_engine.storage_engine import StorageEngine

logger = logging.getLogger(__name__)

CACHE_EXPIRY_SECONDS = 3600  # 1 hour

def should_refresh_data(db: StorageEngine) -> bool:
    """
    Check if the data needs to be refreshed.
    
    Args:
        db: Database connection
        
    Returns:
        bool: True if data should be refreshed
    """
    try:
        result = db.query_data(
            "SELECT timestamp FROM cache_timestamp ORDER BY timestamp DESC LIMIT 1"
        )
        if result.empty:
            return True
            
        last_update = result.iloc[0]['timestamp']
        time_since_update = (datetime.now() - last_update).total_seconds()

        logger.info(f"Time since last update: {time_since_update} seconds")
        
        return time_since_update > CACHE_EXPIRY_SECONDS
    except Exception as e:
        logger.warning(f"Error checking cache timestamp: {e}")
        return True

def refresh_spot_data(
    advisor: AwsSpotAdvisorData,
    db: StorageEngine
) -> None:
    """
    Fetch fresh data and store in database.
    
    Args:
        advisor: Spot advisor data fetcher
        db: Database connection
    """
    logger.info("Fetching fresh spot advisor data...")
    data = advisor.fetch_data()
    
    # Clear existing data
    db.clear_data()
    
    # Store new data
    db.store_data(data)
    logger.info("Spot advisor data updated successfully")

def ensure_fresh_data(
    advisor: AwsSpotAdvisorData,
    db: StorageEngine
) -> None:
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
    except Exception as e:
        logger.error(f"Error ensuring fresh data: {e}")
        raise
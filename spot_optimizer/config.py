"""Configuration management for spot-optimizer."""

import os
from typing import Optional
from appdirs import user_data_dir


class SpotOptimizerConfig:
    """Configuration class for SpotOptimizer settings."""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour
        request_timeout: int = 30,
        max_retries: int = 3,
        spot_advisor_url: str = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
    ):
        """
        Initialize configuration.
        
        Args:
            db_path: Path to database file. If None, uses default user data directory
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            request_timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            spot_advisor_url: URL for AWS Spot Advisor data
        """
        self.db_path = db_path or self._get_default_db_path()
        self.cache_ttl = cache_ttl
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.spot_advisor_url = spot_advisor_url
    
    @staticmethod
    def _get_default_db_path() -> str:
        """
        Get the default database path in user data directory.
        
        Returns:
            str: Path to the database file in the user's data directory
        """
        app_name = "spot-optimizer"
        app_author = "aws-samples"
        data_dir = user_data_dir(app_name, app_author)
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        return os.path.join(data_dir, "spot_advisor_data.db")
    
    @classmethod
    def from_env(cls) -> 'SpotOptimizerConfig':
        """
        Create configuration from environment variables.
        
        Environment variables:
            SPOT_OPTIMIZER_DB_PATH: Database file path
            SPOT_OPTIMIZER_CACHE_TTL: Cache TTL in seconds
            SPOT_OPTIMIZER_REQUEST_TIMEOUT: Request timeout in seconds
            SPOT_OPTIMIZER_MAX_RETRIES: Maximum retry attempts
            SPOT_OPTIMIZER_URL: Spot advisor data URL
        
        Returns:
            SpotOptimizerConfig: Configuration instance
        """
        return cls(
            db_path=os.getenv('SPOT_OPTIMIZER_DB_PATH'),
            cache_ttl=int(os.getenv('SPOT_OPTIMIZER_CACHE_TTL', '3600')),
            request_timeout=int(os.getenv('SPOT_OPTIMIZER_REQUEST_TIMEOUT', '30')),
            max_retries=int(os.getenv('SPOT_OPTIMIZER_MAX_RETRIES', '3')),
            spot_advisor_url=os.getenv(
                'SPOT_OPTIMIZER_URL', 
                'https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json'
            )
        )
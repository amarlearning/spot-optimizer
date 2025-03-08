import logging
from typing import Optional

from spot_optimizer.optimizer_mode import Mode
from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.storage_engine.duckdb_storage_engine import DuckDBStorage
from spot_optimizer.spot_advisor_engine import ensure_fresh_data

logger = logging.getLogger(__name__)

class SpotInstanceOptimizer:
    """Manages spot instance optimization with cached data access."""
    
    _instance: Optional['SpotInstanceOptimizer'] = None
    
    def __init__(self, db_path: str = "spot_advisor_data.db"):
        """Initialize the optimizer with its dependencies."""
        self.spot_advisor = AwsSpotAdvisorData()
        self.db = DuckDBStorage(db_path=db_path)
        self.db.connect()  # Establish initial connection
        
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.disconnect()
    
    @classmethod
    def get_instance(cls, db_path: str = "spot_advisor_data.db") -> 'SpotInstanceOptimizer':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance
    
    def optimize(
        self,
        cores: int,
        memory: int,
        region: str = "us-west-2",
        ssd_only: bool = False,
        arm_instances: bool = True,
        instance_family: list[str] = None,
        emr_version: str = None,
        mode: str = Mode.BALANCED.value,
    ) -> dict:
        """
        Optimize spot instance configuration based on requirements.
        """
        try:
            ensure_fresh_data(self.spot_advisor, self.db)
            return {
                "instances": {
                    "type": "m6id.32xlarge",
                    "count": 1
                },
                "mode": "balanced",
                "total_cores": 128,
                "total_ram": 512
            }
        except Exception as e:
            logger.error(f"Error optimizing instances: {e}")
            raise


def spot_optimiser(
    cores: int,
    memory: int,
    region: str = "us-west-2",
    ssd_only: bool = False,
    arm_instances: bool = True,
    instance_family: list[str] = None,
    emr_version: str = None,
    mode: str = Mode.BALANCED.value,
) -> dict:
    """
    Legacy function that uses the SpotInstanceOptimizer singleton.
    """
    optimizer = SpotInstanceOptimizer.get_instance()
    return optimizer.optimize(
        cores=cores,
        memory=memory,
        region=region,
        ssd_only=ssd_only,
        arm_instances=arm_instances,
        instance_family=instance_family,
        emr_version=emr_version,
        mode=mode,
    )
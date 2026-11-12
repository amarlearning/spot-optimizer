import logging
from typing import Dict, List, Optional

from spot_optimizer.config import SpotOptimizerConfig
from spot_optimizer.optimizer_mode import Mode
from spot_optimizer.query_builder import OptimizationQueryBuilder
from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.storage_engine.duckdb_storage_engine import DuckDBStorage
from spot_optimizer.spot_advisor_engine import ensure_fresh_data
from spot_optimizer.validators import validate_optimization_params


logger = logging.getLogger(__name__)

class SpotOptimizer:
    """Manages spot instance optimization with cached data access."""
    
    _instance: Optional['SpotOptimizer'] = None
    
    def __init__(self, config: Optional[SpotOptimizerConfig] = None):
        """
        Initialize the optimizer with its dependencies.
        
        Args:
            config: Configuration instance. If None, uses default configuration.
        """
        self.config = config or SpotOptimizerConfig.from_env()
        logger.debug(f"Using database path: {self.config.db_path}")
        
        self.spot_advisor = AwsSpotAdvisorData(
            url=self.config.spot_advisor_url,
            request_timeout=self.config.request_timeout,
            max_retries=self.config.max_retries
        )
        self.db = DuckDBStorage(db_path=self.config.db_path)
        self.db.connect()
        self.query_builder = OptimizationQueryBuilder()
        
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.disconnect()
    
    @classmethod
    def get_instance(cls, config: Optional[SpotOptimizerConfig] = None) -> 'SpotOptimizer':
        """
        Get or create the singleton instance.
        
        Args:
            config: Configuration instance. Only used when creating the instance for the first time.
        
        Returns:
            SpotOptimizer: Singleton instance of the optimizer
        """
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def optimize(
        self,
        cores: int,
        memory: int,
        region: str = "us-west-2",
        ssd_only: bool = False,
        arm_instances: bool = True,
        instance_family: List[str] = None,
        emr_version: str = None,
        mode: str = Mode.BALANCED.value,
        top_n: int = 5,
    ) -> Dict:
        """
        Optimize spot instance configuration based on requirements.

        The top-level keys describe the best match; ``candidates`` lists up to
        ``top_n`` ranked instance types so callers can diversify (e.g. as
        EC2 Fleet overrides) instead of relying on a single type.
        """
        validate_optimization_params(cores, memory, mode, top_n)
        
        try:
            ensure_fresh_data(self.spot_advisor, self.db)
            
            # Get instance count range based on mode
            mode_ranges = Mode.calculate_ranges(cores, memory)
            min_instances, max_instances = mode_ranges[mode]
            
            # Build query and parameters using the query builder
            query = self.query_builder.build_optimization_query(
                ssd_only=ssd_only,
                arm_instances=arm_instances,
                instance_family=instance_family
            )
            
            params = self.query_builder.build_query_parameters(
                cores=cores,
                memory=memory,
                region=region,
                instance_family=instance_family,
                min_instances=min_instances,
                max_instances=max_instances,
                top_n=top_n
            )
            
            result = self.db.query_data(query, params)
            
            if len(result) == 0:
                error_msg = self.query_builder.build_error_message_params(
                    cores=cores,
                    memory=memory,
                    region=region,
                    mode=mode,
                    instance_family=instance_family,
                    emr_version=emr_version,
                    ssd_only=ssd_only,
                    arm_instances=arm_instances
                )
                raise ValueError(error_msg)
            
            candidates = [
                {
                    "instances": {
                        "type": row['instance_type'],
                        "count": int(row['instances_needed'])
                    },
                    "total_cores": int(row['total_cores']),
                    "total_ram": int(row['total_memory']),
                    "reliability": {
                        "spot_score": int(row['spot_score']),
                        "interruption_rate": int(row['interruption_rate'])
                    }
                }
                for _, row in result.iterrows()
            ]

            return {**candidates[0], "mode": mode, "candidates": candidates}
            
        except Exception as e:
            logger.error(f"Error optimizing instances: {e}")
            raise

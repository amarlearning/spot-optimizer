import logging
from typing import Dict, List, Optional

from spot_optimizer.optimizer_mode import Mode
from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.storage_engine.duckdb_storage_engine import DuckDBStorage
from spot_optimizer.spot_advisor_engine import ensure_fresh_data
from spot_optimizer.validators import validate_optimization_params


logger = logging.getLogger(__name__)

class SpotOptimizer:
    """Manages spot instance optimization with cached data access."""
    
    _instance: Optional['SpotOptimizer'] = None
    
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
    def get_instance(cls, db_path: str = "spot_advisor_data.db") -> 'SpotOptimizer':
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
        instance_family: List[str] = None,
        emr_version: str = None,
        mode: str = Mode.BALANCED.value,
    ) -> Dict:
        """
        Optimize spot instance configuration based on requirements.
        """
        validate_optimization_params(cores, memory, mode)
        
        try:
            ensure_fresh_data(self.spot_advisor, self.db)
            
            # Get instance count range based on mode
            mode_ranges = Mode.calculate_ranges(cores, memory)
            
            print(mode_ranges)
            print("\n\n")
            
            min_instances, max_instances = mode_ranges[mode]
            
            query = """
                WITH ranked_instances AS (
                    SELECT 
                        i.instance_type,
                        i.cores,
                        i.ram_gb,
                        s.s as spot_score,
                        s.r as interruption_rate,
                        GREATEST(
                            CEIL(CAST(? AS FLOAT) / i.cores),
                            CEIL(CAST(? AS FLOAT) / i.ram_gb)
                        ) as instances_needed
                    FROM instance_types i
                    JOIN spot_advisor s ON i.instance_type = s.instance_types
                    WHERE 
                        s.region = ?
                        AND s.os = 'Linux'
                        {storage_filter}
                        {arch_filter}
                        {family_filter}
                )
                SELECT 
                    *,
                    cores * instances_needed as total_cores,
                    ram_gb * instances_needed as total_memory,
                    ((cores * instances_needed) - ?) * 100.0 / ? as cpu_waste_pct,
                    ((ram_gb * instances_needed) - ?) * 100.0 / ? as memory_waste_pct
                FROM ranked_instances
                WHERE 
                    total_cores >= ?
                    AND total_memory >= ?
                    AND instances_needed BETWEEN ? AND ?  -- Apply mode-specific instance bounds
                ORDER BY 
                    interruption_rate ASC,
                    spot_score DESC,
                    (cpu_waste_pct + memory_waste_pct) ASC
                LIMIT 1
            """
            
            # Add filters based on requirements
            storage_filter = "AND i.storage_type = 'ssd'" if ssd_only else ""
            arch_filter = "AND i.architecture != 'arm64'" if not arm_instances else ""
            family_filter = ""
            
            params = [
                cores, memory, region,  # Basic params
                cores, cores,           # CPU waste calculation
                memory, memory,         # Memory waste calculation
                cores, memory,          # Minimum resource requirements
                min_instances, max_instances  # Mode-specific instance bounds
            ]
            
            if instance_family:
                placeholders = ','.join(['?' for _ in instance_family])
                family_filter = f"AND i.instance_family IN ({placeholders})"
                params.extend(instance_family)
            
            query = query.format(
                storage_filter=storage_filter,
                arch_filter=arch_filter,
                family_filter=family_filter
            )
            
            result = self.db.query_data(query, params)
            
            if len(result) == 0:
                raise ValueError("No suitable instances found matching the requirements")
            
            best_match = result.iloc[0]
            
            return {
                "instances": {
                    "type": best_match['instance_type'],
                    "count": int(best_match['instances_needed'])
                },
                "mode": mode,
                "total_cores": int(best_match['total_cores']),
                "total_ram": int(best_match['total_memory']),
                "reliability": {
                    "spot_score": int(best_match['spot_score']),
                    "interruption_rate": int(best_match['interruption_rate'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing instances: {e}")
            raise

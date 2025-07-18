from typing import Dict, List, Any, Union
import pandas as pd
import math
from spot_optimizer.storage_engine.storage_engine import StorageEngine
from spot_optimizer.exceptions import OptimizationError, ErrorCode
from spot_optimizer.logging_config import get_logger

logger = get_logger(__name__)


def calculate_instance_ranges(cores: int, memory: int, mode: str) -> tuple[int, int]:
    """Calculate min and max instances based on optimization mode."""
    min_instances = math.ceil(cores / 64) if cores > 64 else 1
    max_instances = math.ceil(cores / 8) if cores > 8 else 2

    if mode == "latency":
        max_instances = math.ceil(min_instances * 1.5)
    elif mode == "fault_tolerance":
        min_instances = math.ceil(max_instances / 2)

    return min_instances, max_instances


class SpotOptimizerCore:
    """Handles the core logic for spot instance optimization."""

    def __init__(self, db: StorageEngine):
        """Initialize the optimizer with its dependencies.
        :param db: The database storage engine.
        """
        self.db: StorageEngine = db

    def optimize(
        self,
        cores: int,
        memory: int,
        region: str,
        ssd_only: bool,
        arm_instances: bool,
        instance_family: List[str],
        emr_version: str,
        mode: str,
    ) -> Dict:
        """Optimize spot instance configuration based on requirements."""
        try:
            min_instances, max_instances = calculate_instance_ranges(
                cores, memory, mode
            )

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
                    AND instances_needed BETWEEN ? AND ?
                ORDER BY
                    interruption_rate ASC,
                    spot_score DESC,
                    (cpu_waste_pct + memory_waste_pct) ASC
                LIMIT 1
            """

            # Add filters based on requirements
            storage_filter: str = "AND i.storage_type = 'ssd'" if ssd_only else ""
            arch_filter: str = (
                "AND i.architecture != 'arm64'" if not arm_instances else ""
            )
            family_filter: str = ""

            params: List[Union[str, int, float]] = [
                cores,
                memory,
                region,
                cores,
                cores,
                memory,
                memory,
                cores,
                memory,
                min_instances,
                max_instances,
            ]

            if instance_family:
                placeholders: str = ",".join(["?" for _ in instance_family])
                family_filter = f"AND i.instance_family IN ({placeholders})"
                params.extend(instance_family)

            query = query.format(
                storage_filter=storage_filter,
                arch_filter=arch_filter,
                family_filter=family_filter,
            )

            result: pd.DataFrame = self.db.query_data(query, params)

            if len(result) == 0:
                error_params: Dict[str, Any] = {
                    "cores": cores,
                    "memory": memory,
                    "region": region,
                    "mode": mode,
                }
                if instance_family:
                    error_params["instance_family"] = instance_family
                    error_params["emr_version"] = emr_version
                if ssd_only:
                    error_params["ssd_only"] = ssd_only
                if not arm_instances:
                    error_params["arm_instances"] = arm_instances
                param_strs: List[str] = [
                    f"{key} = {value}" for key, value in error_params.items()
                ]
                error_msg: str = (
                    "No suitable instances found matching for "
                    + " and ".join(param_strs)
                )
                raise OptimizationError(error_msg, ErrorCode.NO_SUITABLE_INSTANCES)

            best_match: pd.Series = result.iloc[0]

            return {
                "instances": {
                    "type": best_match["instance_type"],
                    "count": int(best_match["instances_needed"]),
                },
                "mode": mode,
                "total_cores": int(best_match["total_cores"]),
                "total_ram": int(best_match["total_memory"]),
                "reliability": {
                    "spot_score": int(best_match["spot_score"]),
                    "interruption_rate": int(best_match["interruption_rate"]),
                },
            }

        except Exception as e:
            raise OptimizationError(
                f"Error optimizing instances: {e}",
                error_code=ErrorCode.OPTIMIZATION_FAILED,
                cause=e,
            )

import logging

from spot_optimizer.optimiser_mode import Mode

from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.storage_engine.duckdb_storage import DuckDBStorage
from spot_optimizer.spot_advisor_engine import fetch_and_store_spot_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cluster_optimiser(
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
    Optimize the spot instance configuration based on the provided parameters.

    :param cores: Total number of CPU cores required.
    :param memory: Total amount of RAM required (in GB).
    :param region: AWS region to find instances in.
    :param ssd_only: Filter for SSD-backed instances.
    :param arm_instances: Include ARM-based instances if True.
    :param instance_family: List of instance families (e.g., ['m5', 'c5', 'r5']).
    :param emr_version: Optional EMR version for EMR workloads (e.g., '6.10.0').
    :param mode: Optimization mode: "latency", "fault_tolerance", or "balanced".
    :return: The recommended instance configuration that meets the specified requirements.
    """

    with DuckDBStorage(db_path="spot_advisor_data.db") as db_instance:
        spot_advisor_data_instance = AwsSpotAdvisorData(cache_expiry=3600)
        fetch_and_store_spot_data(spot_advisor_data_instance, db_instance)

        query = """
            SELECT * FROM instance_types 
            WHERE cores >= ? AND ram_gb >= ?
        """
        params = [cores, memory]

        if ssd_only:
            query += " AND storage_type LIKE '%SSD%'"

        if not arm_instances:
            query += " AND architecture != 'arm64'"

        if instance_family:
            query += " AND instance_family = ?"
            params.append(instance_family)

        if emr_version:
            query += " AND emr_compatible = TRUE AND emr_min_version <= ?"
            params.append(emr_version)

        # Add ordering based on mode
        if mode == Mode.LATENCY.value:
            query += " ORDER BY cores DESC, ram_gb DESC"
        elif mode == Mode.FAULT_TOLERANCE.value:
            query += " ORDER BY cores ASC, ram_gb ASC"
        else:  # balanced
            query += " ORDER BY (ABS(cores - ?) + ABS(ram_gb - ?)) ASC"
            params.extend([cores, memory])

        query += " LIMIT 1"

        result = db_instance.query_data(query, params)
        
        if result.empty:
            return {"error": "No suitable instance type found."}

        instance = result.iloc[0]
        count = max(
            cores // instance["cores"],
            int(memory / instance["ram_gb"])
        )
        
        count = int(count)
        total_cores = int(count * instance["cores"])
        total_ram = int(count * instance["ram_gb"])

        return {
            "instances": {
                "type": instance["instance_type"],
                "count": count
            },
            "mode": mode,
            "total_cores": total_cores,
            "total_ram": total_ram
        }

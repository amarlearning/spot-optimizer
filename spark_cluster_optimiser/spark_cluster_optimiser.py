import logging

from spark_cluster_optimiser.optimiser_mode import Mode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cluster_optimiser(
    cores: int,
    memory: int,
    region: str = "us-west-2",
    ssd_only: bool = False,
    arm_instances: bool = True,
    emr_version: str = "6.10.0",
    mode: str = Mode.BALANCED.value,
) -> int:
    """
    Optimize the cluster configuration based on the provided parameters.

    :param cores: Total number of cores required.
    :param memory: Total amount of RAM required (in GB).
    :param region: AWS region to find instances in.
    :param ssd_only: Filter for SSD-backed instances.
    :param arm_instances: Include ARM-based instances if True.
    :param emr_version: EMR version compatibility filter (e.g., "6.10.0").
    :param mode: Optimization mode: "latency", "fault_tolerance", or "balanced".
    :param spot_advisor_data_instance: Instance of AwsSpotAdvisorData.
    :param db_instance: Instance of DuckDBStorage.
    :return: The number of instances required to meet the specified core and memory requirements.
    """

    # try:
    #     spot_advisor_data_instance = AwsSpotAdvisorData(cache_expiry=3600)
    #     db_instance = DuckDBStorage(db_path="spot_advisor_data.db")
    #     fetch_and_store_spot_data(spot_advisor_data_instance, db_instance)

    #     print(db_instance.query_data("SELECT * FROM global_rate LIMIT 1"))
    #     print(db_instance.query_data("SELECT * FROM cache_timestamp LIMIT 1"))
    #     print(db_instance.query_data("SELECT * FROM instance_types LIMIT 1"))
    #     print(db_instance.query_data("SELECT * FROM ranges LIMIT 1"))

    # except Exception as e:
    #     logger.error(
    #         f"An error occurred during finding optimized cluster : {e}"
    #     )
    #     raise

    return 6

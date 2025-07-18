from typing import Dict, List, Optional
from .spot_optimizer import SpotOptimizerFacade
from .optimizer_mode import Mode


def optimize(
    cores: int,
    memory: int,
    region: str = "us-west-2",
    ssd_only: bool = False,
    arm_instances: bool = True,
    instance_family: Optional[List[str]] = None,
    emr_version: Optional[str] = None,
    mode: str = Mode.BALANCED.value,
) -> Dict:
    """
    Public API function to get spot instance recommendations.

    Args:
        cores: Total number of CPU cores required.
        memory: Total amount of RAM required (in GB).
        region: AWS region to find instances in.
        ssd_only: Filter for SSD-backed instances.
        arm_instances: Include ARM-based instances if True.
        instance_family: Filter by instance family.
        emr_version: Optional EMR version for EMR workloads.
        mode: Optimization mode.

    Returns:
        A dictionary containing the recommended instance type, count, and other details.
    """
    optimizer_facade = SpotOptimizerFacade.get_instance()
    with optimizer_facade as facade:
        return facade.optimize(
            cores=cores,
            memory=memory,
            region=region,
            ssd_only=ssd_only,
            arm_instances=arm_instances,
            instance_family=instance_family,
            emr_version=emr_version,
            mode=mode,
        )

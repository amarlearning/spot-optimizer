from spot_optimizer.optimizer_mode import Mode
from spot_optimizer.spot_optimizer import SpotOptimizer

default_optimizer = SpotOptimizer()

__all__ = ['optimize', 'Mode', 'SpotOptimizer']

def optimize(
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
    
    Args:
        cores: Number of CPU cores required
        memory: Amount of RAM required (in GB)
        region: AWS region (default: "us-west-2")
        ssd_only: Whether to only consider instances with SSD storage
        arm_instances: Whether to include ARM-based instances
        instance_family: List of instance families to consider
        emr_version: EMR version if using with EMR
        mode: Optimization mode (default: BALANCED)
        
    Returns:
        dict: Optimized instance configuration
    
    Example:
        >>> from spot_optimizer import optimize
        >>> config = optimize(
        ...     cores=8,
        ...     memory=32,
        ...     region="us-east-1"
        ... )
        >>> print(config)
        {
            "instances": {
                "type": "m6i.2xlarge",
                "count": 1
            },
            "mode": "balanced",
            "total_cores": 8,
            "total_ram": 32
        }
    """
    return default_optimizer.optimize(
        cores=cores,
        memory=memory,
        region=region,
        ssd_only=ssd_only,
        arm_instances=arm_instances,
        instance_family=instance_family,
        emr_version=emr_version,
        mode=mode,
    )

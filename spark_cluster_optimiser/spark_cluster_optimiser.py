from enum import Enum

class Mode(Enum):
    LATENCY = "latency"
    BALANCED = "balanced"
    FAULT_tolerance = "fault_tolerance"

def cluster_optimiser(
        cores: int,                         # Total number of cores required
        memory: int,                        # Total amount of RAM required (in GB)
        ssd_only: bool = False,             # Filter for SSD-backed instances
        arm_instances: bool = True,         # Include ARM-based instances if True
        emr_version: str = "6.10.0",        # EMR version compatibility filter (e.g., "6.10.0")
        mode: str = Mode.BALANCED.value     # Optimization mode: "latency", "fault_tolerance", or "balanced"
    ) -> int:
    return cores + memory
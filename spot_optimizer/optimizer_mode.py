from enum import Enum
from typing import Dict, Tuple


class Mode(Enum):
    LATENCY = "latency"
    BALANCED = "balanced"
    FAULT_TOLERANCE = "fault_tolerance"

    @staticmethod
    def calculate_ranges(total_cores: int, total_memory: int) -> Dict[str, Tuple[int, int]]:
        """
        Calculate instance count ranges for different modes based on resource requirements.
        
        Small workloads (base_count <= 4):
            - Latency: 1 instance
            - Balanced: 2 instances
            - Fault Tolerance: 3-4 instances
        
        Large workloads (base_count > 4):
            - Latency: up to 25% of base
            - Balanced: 25% to 100% of base
            - Fault Tolerance: 100% to 200% of base
        
        Args:
            total_cores: Total CPU cores required
            total_memory: Total memory required (GB)
        """
        base_scale = max(
            total_cores / 16,
            total_memory / 64
        )
        
        base_count = max(2, int(base_scale))

        if base_count <= 4:
            return {
                Mode.LATENCY.value: (1, 1),
                Mode.BALANCED.value: (2, 2),
                Mode.FAULT_TOLERANCE.value: (3, 4)
            }
        
        latency_max = max(4, base_count // 4)
        balanced_min = latency_max + 1
        balanced_max = base_count
        fault_min = balanced_max + 1
        fault_max = base_count * 2

        return {
            Mode.LATENCY.value: (1, latency_max),
            Mode.BALANCED.value: (balanced_min, balanced_max),
            Mode.FAULT_TOLERANCE.value: (fault_min, fault_max)
        }

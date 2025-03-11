from enum import Enum
from typing import Dict, Tuple


class Mode(Enum):
    LATENCY = "latency"
    BALANCED = "balanced"
    FAULT_TOLERANCE = "fault_tolerance"

    @staticmethod
    def calculate_ranges(total_cores: int, total_memory: int) -> Dict[str, Tuple[int, int]]:
        """
        Calculate non-overlapping instance count ranges for different modes.
        Returns dict with (min_instances, max_instances) for each mode.
        """
        base_scale = max(
            total_cores / 16,
            total_memory / 64
        )
        
        base_count = max(2, int(base_scale))

        return {
            Mode.LATENCY.value: (
                1,
                min(4, base_count//2)
            ),
            Mode.BALANCED.value: (
                min(4, base_count//2) + 1,
                base_count
            ),
            Mode.FAULT_TOLERANCE.value: (
                base_count + 1,
                base_count * 2
            )
        }

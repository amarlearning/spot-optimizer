import pytest
from spot_optimizer.optimizer_mode import Mode


def test_optimizer_modes():
    """Test that optimizer modes have correct values."""
    assert Mode.LATENCY.value == "latency"
    assert Mode.BALANCED.value == "balanced"
    assert Mode.FAULT_TOLERANCE.value == "fault_tolerance"
    assert len(Mode) == 3
    
    
@pytest.mark.parametrize("cores, memory, expected_ranges", [
    # Small workload - ranges might overlap, that's okay
    (4, 16, {
        'latency': (1, 1),
        'balanced': (2, 2),
        'fault_tolerance': (3, 4)
    }),
    (8, 32, {
        'latency': (1, 1),
        'balanced': (2, 2),
        'fault_tolerance': (3, 4)
    }),
    
    # Medium workload
    (64, 256, {
        'latency': (1, 2),
        'balanced': (3, 4),
        'fault_tolerance': (5, 8)
    }),
    (128, 512, {
        'latency': (1, 4),
        'balanced': (5, 8),
        'fault_tolerance': (9, 16)
    }),
    
    # Large workload
    (400, 2000, {
        'latency': (1, 4),
        'balanced': (5, 31),
        'fault_tolerance': (32, 62)
    }),
    (1000, 4000, {
        'latency': (1, 4),
        'balanced': (5, 62),
        'fault_tolerance': (63, 124)
    })
])
def test_mode_ranges(cores, memory, expected_ranges):
    """Test mode range calculations for various workload sizes."""
    ranges = Mode.calculate_ranges(cores, memory)
    
    # Basic validation
    assert len(ranges) == 3
    assert all(mode.value in ranges for mode in Mode)
    
    # Check each mode's range
    for mode, (min_instances, max_instances) in ranges.items():
        assert min_instances <= max_instances, f"Invalid range for {mode}: {min_instances} > {max_instances}"
        assert min_instances > 0, f"Min instances should be positive for {mode}"
        
        expected_min, expected_max = expected_ranges[mode]
        assert min_instances == expected_min, f"Unexpected min instances for {mode}"
        assert max_instances == expected_max, f"Unexpected max instances for {mode}"

def test_small_workload_overlap_acceptable():
    """Test that small workloads can have overlapping ranges."""
    ranges = Mode.calculate_ranges(2, 8)
    
    # For very small workloads, all modes might suggest similar ranges
    assert ranges[Mode.LATENCY.value][0] == 1  # Latency should always start at 1
    # Other modes might overlap for small workloads, and that's okay

def test_large_workload_distinct_ranges():
    """Test that large workloads have distinct, non-overlapping ranges."""
    ranges = Mode.calculate_ranges(256, 1024)
    
    latency_max = ranges[Mode.LATENCY.value][1]
    balanced_min = ranges[Mode.BALANCED.value][0]
    balanced_max = ranges[Mode.BALANCED.value][1]
    fault_min = ranges[Mode.FAULT_TOLERANCE.value][0]
    
    # Check for non-overlapping ranges
    assert balanced_min > latency_max, "Balanced range should start after latency range ends"
    assert fault_min > balanced_max, "Fault tolerance range should start after balanced range ends"

def test_extreme_values():
    """Test handling of extreme resource requirements."""
    # Very large values
    large_ranges = Mode.calculate_ranges(2000, 8000)
    assert large_ranges[Mode.LATENCY.value][1] <= 4, "Latency mode should still be capped for large values"
    
    # Very small values
    small_ranges = Mode.calculate_ranges(1, 4)
    assert small_ranges[Mode.LATENCY.value][0] == 1, "Latency mode should always start at 1"
    assert all(min_val > 0 for min_val, _ in small_ranges.values()), "All min values should be positive"

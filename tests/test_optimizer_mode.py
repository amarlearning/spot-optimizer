from spot_optimizer.optimizer_mode import Mode


def test_optimizer_modes():
    """Test that optimizer modes have correct values."""
    assert Mode.LATENCY.value == "latency"
    assert Mode.BALANCED.value == "balanced"
    assert Mode.FAULT_TOLERANCE.value == "fault_tolerance"
    assert len(Mode) == 3  # Ensure we have exactly 3 modes

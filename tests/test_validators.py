import pytest
from spot_optimizer.validators import (
    validate_cores,
    validate_memory,
    validate_mode,
    validate_optimization_params,
)
from spot_optimizer.optimizer_mode import Mode


def test_validate_cores_valid():
    """Test valid core values."""
    # These should not raise exceptions
    validate_cores(1)
    validate_cores(16)
    validate_cores(1024)


@pytest.mark.parametrize(
    "cores,error_msg",
    [
        (0, "cores must be positive"),
        (-1, "cores must be positive"),
    ],
)
def test_validate_cores_invalid(cores, error_msg):
    """Test invalid core values."""
    with pytest.raises(ValueError, match=error_msg):
        validate_cores(cores)


def test_validate_memory_valid():
    """Test valid memory values."""
    # These should not raise exceptions
    validate_memory(1)
    validate_memory(32)
    validate_memory(4096)


@pytest.mark.parametrize(
    "memory,error_msg",
    [
        (0, "memory must be positive"),
        (-1, "memory must be positive"),
    ],
)
def test_validate_memory_invalid(memory, error_msg):
    """Test invalid memory values."""
    with pytest.raises(ValueError, match=error_msg):
        validate_memory(memory)


def test_validate_mode_valid():
    """Test valid optimization modes."""
    # Test all valid modes from the Mode enum
    for mode in Mode:
        validate_mode(mode.value)  # Should not raise exception


def test_validate_mode_invalid():
    """Test invalid optimization mode."""
    with pytest.raises(ValueError, match="Invalid mode"):
        validate_mode("invalid_mode")


def test_validate_optimization_params_valid():
    """Test valid parameter combinations."""
    # These should not raise exceptions
    validate_optimization_params(cores=8, memory=32, mode=Mode.BALANCED.value)
    validate_optimization_params(cores=1024, memory=4096, mode=Mode.BALANCED.value)


@pytest.mark.parametrize(
    "cores,memory,mode,expected_error",
    [
        (0, 32, Mode.BALANCED.value, "cores must be positive"),
        (8, 0, Mode.BALANCED.value, "memory must be positive"),
        (8, 32, "invalid_mode", "Invalid mode"),
    ],
)
def test_validate_optimization_params_invalid(cores, memory, mode, expected_error):
    """Test invalid parameter combinations."""
    with pytest.raises(ValueError, match=expected_error):
        validate_optimization_params(cores, memory, mode)

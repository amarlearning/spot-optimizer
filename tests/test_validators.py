import pytest
from spot_optimizer.validators import (
    validate_cores,
    validate_memory,
    validate_optimization_params,
)
from spot_optimizer.exceptions import ValidationError


def test_validate_cores_valid():
    """Test valid core values."""
    validate_cores(1)
    validate_cores(1024)


@pytest.mark.parametrize("cores", [0, -1])
def test_validate_cores_invalid(cores: int):
    """Test invalid core values."""
    with pytest.raises(ValidationError, match="Cores must be positive"):
        validate_cores(cores)


def test_validate_memory_valid():
    """Test valid memory values."""
    validate_memory(1)
    validate_memory(4096)


@pytest.mark.parametrize("memory", [0, -1])
def test_validate_memory_invalid(memory: int):
    """Test invalid memory values."""
    with pytest.raises(ValidationError, match="Memory must be positive"):
        validate_memory(memory)


def test_validate_optimization_params_valid():
    """Test valid parameter combinations."""
    validate_optimization_params(cores=8, memory=32)
    validate_optimization_params(cores=1024, memory=4096)


@pytest.mark.parametrize(
    "cores,memory,expected_error",
    [
        (0, 32, "Cores must be positive"),
        (8, 0, "Memory must be positive"),
        (-1, -1, "Cores must be positive"),
    ],
)
def test_validate_optimization_params_invalid(
    cores: int, memory: int, expected_error: str
):
    """Test invalid parameter combinations."""
    with pytest.raises(ValidationError, match=expected_error):
        validate_optimization_params(cores, memory)

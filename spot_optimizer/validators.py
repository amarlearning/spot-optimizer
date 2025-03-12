from typing import List, Optional
from spot_optimizer.optimizer_mode import Mode

def validate_cores(cores: int) -> None:
    """Validate CPU cores requirement."""
    if cores <= 0:
        raise ValueError("cores must be positive")

def validate_memory(memory: int) -> None:
    """Validate memory requirement in GB."""
    if memory <= 0:
        raise ValueError("memory must be positive")

def validate_mode(mode: str) -> None:
    """Validate optimization mode."""
    try:
        Mode(mode)
    except ValueError:
        valid_modes = [m.value for m in Mode]
        raise ValueError(f"Invalid mode. Must be one of: {', '.join(valid_modes)}")

def validate_optimization_params(
    cores: int,
    memory: int,
    mode: str = Mode.BALANCED.value,
) -> None:
    """Validate all optimization parameters."""
    validate_cores(cores)
    validate_memory(memory)
    validate_mode(mode) 
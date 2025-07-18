from spot_optimizer.optimizer_mode import Mode
from spot_optimizer.exceptions import ErrorCode, raise_validation_error


def validate_cores(cores: int) -> None:
    """Validate CPU cores requirement."""
    if cores <= 0:
        raise_validation_error(
            "cores must be positive",
            error_code=ErrorCode.VALIDATION_INVALID_VALUE,
            validation_context={"cores": cores, "minimum_required": 1},
            suggestions=[
                "Provide a positive integer for CPU cores",
                "Ensure cores is at least 1",
                "Check if the input value is correct",
            ],
        )


def validate_memory(memory: int) -> None:
    """Validate memory requirement in GB."""
    if memory <= 0:
        raise_validation_error(
            "memory must be positive",
            error_code=ErrorCode.VALIDATION_INVALID_VALUE,
            validation_context={"memory_gb": memory, "minimum_required": 1},
            suggestions=[
                "Provide a positive integer for memory in GB",
                "Ensure memory is at least 1 GB",
                "Check if the input value is correct",
            ],
        )


def validate_mode(mode: str) -> None:
    """Validate optimization mode."""
    try:
        Mode(mode)
    except ValueError as e:
        valid_modes = [m.value for m in Mode]
        raise_validation_error(
            f"Invalid mode. Must be one of: {', '.join(valid_modes)}",
            error_code=ErrorCode.VALIDATION_INVALID_VALUE,
            validation_context={"provided_mode": mode, "valid_modes": valid_modes},
            suggestions=[
                f"Use one of the valid modes: {', '.join(valid_modes)}",
                "Check the spelling of the mode parameter",
                "Ensure the mode is a valid string",
            ],
            cause=e,
        )


def validate_optimization_params(
    cores: int,
    memory: int,
    mode: str = Mode.BALANCED.value,
) -> None:
    """Validate all optimization parameters."""
    validate_cores(cores)
    validate_memory(memory)
    validate_mode(mode)

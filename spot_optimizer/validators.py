from spot_optimizer.exceptions import ErrorCode, ValidationError


def validate_cores(cores: int) -> None:
    """Validate CPU cores requirement."""
    if cores <= 0:
        raise ValidationError(
            "Cores must be positive",
            error_code=ErrorCode.VALIDATION_INVALID_VALUE,
            context={"cores": cores, "minimum_required": 1},
            suggestions=[
                "Provide a positive integer for CPU cores",
                "Ensure cores is at least 1",
            ],
        )


def validate_memory(memory: int) -> None:
    """Validate memory requirement in GB."""
    if memory <= 0:
        raise ValidationError(
            "Memory must be positive",
            error_code=ErrorCode.VALIDATION_INVALID_VALUE,
            context={"memory_gb": memory, "minimum_required": 1},
            suggestions=[
                "Provide a positive integer for memory in GB",
                "Ensure memory is at least 1 GB",
            ],
        )


def validate_optimization_params(cores: int, memory: int) -> None:
    """Validate all optimization parameters."""
    validate_cores(cores)
    validate_memory(memory)

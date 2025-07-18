"""Custom exception hierarchy for the Spot Optimizer application.

This module provides a structured hierarchy of exceptions with error codes,
context information, and actionable suggestions for error handling.
"""

from typing import Any, Dict, Optional, Union
from enum import Enum
from spot_optimizer.logging_config import get_logger

logger = get_logger(__name__)


class ErrorCode(Enum):
    """Error codes for programmatic error handling."""

    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    CONFIGURATION_ERROR = 1001
    INITIALIZATION_ERROR = 1002

    # Validation errors (2000-2999)
    INVALID_CORES = 2000
    INVALID_MEMORY = 2001
    INVALID_MODE = 2002
    INVALID_REGION = 2003
    INVALID_URL = 2004
    INVALID_TABLE_NAME = 2005
    INVALID_PARAMETERS = 2006
    VALIDATION_INVALID_VALUE = 2007
    VALIDATION_INVALID_URL = 2008

    # Storage errors (3000-3999)
    DATABASE_CONNECTION_ERROR = 3000
    DATABASE_QUERY_ERROR = 3001
    DATABASE_STORE_ERROR = 3002
    DATABASE_CLEAR_ERROR = 3003
    TABLE_CREATION_ERROR = 3004
    STORAGE_QUERY_FAILED = 3005

    # Optimization errors (4000-4999)
    NO_SUITABLE_INSTANCES = 4000
    OPTIMIZATION_FAILED = 4001
    INSTANCE_FILTERING_ERROR = 4002

    # Network errors (5000-5999)
    NETWORK_REQUEST_ERROR = 5000
    NETWORK_TIMEOUT_ERROR = 5001
    NETWORK_PARSE_ERROR = 5002
    DATA_FETCH_ERROR = 5003
    NETWORK_REQUEST_FAILED = 5004

    # Cache/Data errors (6000-6999)
    CACHE_REFRESH_ERROR = 6000
    DATA_VALIDATION_ERROR = 6001
    STALE_DATA_ERROR = 6002
    DATA_INVALID_FORMAT = 6003
    DATA_REFRESH_FAILED = 6004


class SpotOptimizerError(Exception):
    """Base exception for all Spot Optimizer errors.

    This exception provides structured error handling with:
    - Error codes for programmatic handling
    - Context information for debugging
    - Actionable suggestions for resolution
    - Support for exception chaining
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[Union[str, list]] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize the base exception.

        Args:
            message: Human-readable error message
            error_code: Programmatic error code
            context: Additional context information
            suggestions: Actionable suggestions for resolution
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.suggestions = suggestions
        self.cause = cause

        # Set the cause for proper exception chaining
        if cause:
            self.__cause__ = cause

    def __str__(self) -> str:
        """Return formatted error message with context."""
        parts = [super().__str__()]

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        if self.suggestions:
            if isinstance(self.suggestions, list):
                suggestions_str = "; ".join(self.suggestions)
            else:
                suggestions_str = self.suggestions
            parts.append(f"Suggestions: {suggestions_str}")

        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": super().__str__(),
            "context": self.context,
            "suggestions": self.suggestions,
            "cause": str(self.cause) if self.cause else None,
        }


class ValidationError(SpotOptimizerError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INVALID_PARAMETERS,
        invalid_value: Any = None,
        valid_values: Optional[Union[str, list]] = None,
        **kwargs,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            error_code: Specific validation error code
            invalid_value: The invalid value that caused the error
            valid_values: Valid values or range description
            **kwargs: Additional arguments for base class
        """
        context = kwargs.get("context", {})
        if invalid_value is not None:
            context["invalid_value"] = invalid_value
        if valid_values is not None:
            context["valid_values"] = valid_values

        kwargs["context"] = context
        super().__init__(message, error_code, **kwargs)


class ConfigurationError(SpotOptimizerError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.CONFIGURATION_ERROR,
        config_key: Optional[str] = None,
        **kwargs,
    ):
        """Initialize configuration error.

        Args:
            message: Error message
            error_code: Specific configuration error code
            config_key: The configuration key that caused the error
            **kwargs: Additional arguments for base class
        """
        context = kwargs.get("context", {})
        if config_key:
            context["config_key"] = config_key

        kwargs["context"] = context
        super().__init__(message, error_code, **kwargs)


class StorageError(SpotOptimizerError):
    """Raised when database/storage operations fail."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_CONNECTION_ERROR,
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        **kwargs,
    ):
        """Initialize storage error.

        Args:
            message: Error message
            error_code: Specific storage error code
            operation: The database operation that failed
            table_name: The table involved in the operation
            **kwargs: Additional arguments for base class
        """
        context = kwargs.get("context", {})
        if operation:
            context["operation"] = operation
        if table_name:
            context["table_name"] = table_name

        kwargs["context"] = context
        super().__init__(message, error_code, **kwargs)


class OptimizationError(SpotOptimizerError):
    """Raised when optimization process fails."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.OPTIMIZATION_FAILED,
        optimization_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Initialize optimization error.

        Args:
            message: Error message
            error_code: Specific optimization error code
            optimization_params: Parameters used in failed optimization
            **kwargs: Additional arguments for base class
        """
        context = kwargs.get("context", {})
        if optimization_params:
            context.update(optimization_params)

        kwargs["context"] = context
        super().__init__(message, error_code, **kwargs)


class NetworkError(SpotOptimizerError):
    """Raised when network operations fail."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.NETWORK_REQUEST_ERROR,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs,
    ):
        """Initialize network error.

        Args:
            message: Error message
            error_code: Specific network error code
            url: URL involved in the failed request
            status_code: HTTP status code if applicable
            **kwargs: Additional arguments for base class
        """
        context = kwargs.get("context", {})
        if url:
            context["url"] = url
        if status_code:
            context["status_code"] = status_code

        kwargs["context"] = context
        super().__init__(message, error_code, **kwargs)


class DataError(SpotOptimizerError):
    """Raised when data operations fail."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATA_VALIDATION_ERROR,
        data_source: Optional[str] = None,
        **kwargs,
    ):
        """Initialize data error.

        Args:
            message: Error message
            error_code: Specific data error code
            data_source: Source of the problematic data
            **kwargs: Additional arguments for base class
        """
        context = kwargs.get("context", {})
        if data_source:
            context["data_source"] = data_source

        kwargs["context"] = context
        super().__init__(message, error_code, **kwargs)


# Convenience functions for common error scenarios
def raise_validation_error(
    message: str,
    error_code: ErrorCode = ErrorCode.INVALID_PARAMETERS,
    validation_context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[list] = None,
    cause: Optional[Exception] = None,
) -> None:
    """Raise a standardized validation error.

    Args:
        message: Error message
        error_code: Specific validation error code
        validation_context: Context information for the validation error
        suggestions: List of suggested solutions
        cause: Original exception that caused this error
    """
    error = ValidationError(
        message=message,
        error_code=error_code,
        context=validation_context,
        suggestions=suggestions,
        cause=cause,
    )
    logger.error("Validation error raised: %s", str(error))
    raise error


def raise_storage_error(
    message: str,
    error_code: ErrorCode = ErrorCode.DATABASE_CONNECTION_ERROR,
    storage_context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[list] = None,
    cause: Optional[Exception] = None,
) -> None:
    """Raise a standardized storage error.

    Args:
        message: Error message
        error_code: Specific storage error code
        storage_context: Context information for the storage error
        suggestions: List of suggested solutions
        cause: Original exception that caused this error
    """
    error = StorageError(
        message=message,
        error_code=error_code,
        context=storage_context,
        suggestions=suggestions,
        cause=cause,
    )
    logger.error("Storage error raised: %s", str(error))
    raise error


def raise_optimization_error(
    reason: str, params: Dict[str, Any], cause: Optional[Exception] = None
) -> None:
    """Raise a standardized optimization error.

    Args:
        reason: Reason for optimization failure
        params: Parameters used in failed optimization
        cause: Original exception that caused this error
    """
    if "no suitable instances" in reason.lower():
        error_code = ErrorCode.NO_SUITABLE_INSTANCES
        suggestions = [
            "Try adjusting your requirements (cores, memory, region)",
            "Consider enabling ARM instances",
            "Try a different optimization mode",
            "Check if the region has available instance types",
        ]
    else:
        error_code = ErrorCode.OPTIMIZATION_FAILED
        suggestions = [
            "Check your optimization parameters",
            "Verify data is fresh and available",
            "Try a different region or instance family",
        ]

    error = OptimizationError(
        message=f"Optimization failed: {reason}",
        error_code=error_code,
        optimization_params=params,
        suggestions=suggestions,
        cause=cause,
    )
    logger.error("Optimization error raised: %s", str(error))
    raise error


def raise_network_error(
    message: str,
    error_code: ErrorCode = ErrorCode.NETWORK_REQUEST_ERROR,
    network_context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[list] = None,
    cause: Optional[Exception] = None,
) -> None:
    """Raise a standardized network error.

    Args:
        message: Error message
        error_code: Specific network error code
        network_context: Context information for the network error
        suggestions: List of suggested solutions
        cause: Original exception that caused this error
    """
    error = NetworkError(
        message=message,
        error_code=error_code,
        context=network_context,
        suggestions=suggestions,
        cause=cause,
    )
    logger.error("Network error raised: %s", str(error))
    raise error


def raise_data_error(
    message: str,
    error_code: ErrorCode = ErrorCode.DATA_VALIDATION_ERROR,
    data_context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[list] = None,
    cause: Optional[Exception] = None,
) -> None:
    """Raise a standardized data error.

    Args:
        message: Error message
        error_code: Specific data error code
        data_context: Context information for the data error
        suggestions: List of suggested solutions
        cause: Original exception that caused this error
    """
    error = DataError(
        message=message,
        error_code=error_code,
        context=data_context,
        suggestions=suggestions,
        cause=cause,
    )
    logger.error("Data error raised: %s", str(error))
    raise error


def raise_configuration_error(
    message: str,
    error_code: ErrorCode = ErrorCode.CONFIGURATION_ERROR,
    config_context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[list] = None,
    cause: Optional[Exception] = None,
) -> None:
    """Raise a standardized configuration error.

    Args:
        message: Error message
        error_code: Specific configuration error code
        config_context: Context information for the configuration error
        suggestions: List of suggested solutions
        cause: Original exception that caused this error
    """
    error = ConfigurationError(
        message=message,
        error_code=error_code,
        context=config_context,
        suggestions=suggestions,
        cause=cause,
    )
    logger.error("Configuration error raised: %s", str(error))
    raise error

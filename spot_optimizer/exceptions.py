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

    :param message: Human-readable error message
    :param error_code: Programmatic error code
    :param context: Additional context information
    :param suggestions: Actionable suggestions for resolution
    :param cause: Original exception that caused this error
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[Union[str, list]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.suggestions = suggestions
        self.cause = cause

        # Set the cause for proper exception chaining
        if cause:
            self.__cause__ = cause

        logger.error("%s: %s", self.__class__.__name__, message, exc_info=True)

    def __str__(self) -> str:
        """Return formatted error message with context."""
        parts = [super().__str__()]

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

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
        """
        :param message: Error message
        :param error_code: Specific validation error code
        :param invalid_value: The invalid value that caused the error
        :param valid_values: Valid values or range description
        :param kwargs: Additional arguments for base class
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
        """
        :param message: Error message
        :param error_code: Specific configuration error code
        :param config_key: The configuration key that caused the error
        :param kwargs: Additional arguments for base class
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
        """
        :param message: Error message
        :param error_code: Specific storage error code
        :param operation: The database operation that failed
        :param table_name: The table involved in the operation
        :param kwargs: Additional arguments for base class
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
        """
        :param message: Error message
        :param error_code: Specific optimization error code
        :param optimization_params: Parameters used in failed optimization
        :param kwargs: Additional arguments for base class
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
        """
        :param message: Error message
        :param error_code: Specific network error code
        :param url: URL involved in the failed request
        :param status_code: HTTP status code if applicable
        :param kwargs: Additional arguments for base class
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
        """
        :param message: Error message
        :param error_code: Specific data error code
        :param data_source: Source of the problematic data
        :param kwargs: Additional arguments for base class
        """
        context = kwargs.get("context", {})
        if data_source:
            context["data_source"] = data_source

        kwargs["context"] = context
        super().__init__(message, error_code, **kwargs)

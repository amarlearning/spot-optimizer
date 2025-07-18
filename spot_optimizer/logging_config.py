"""
Centralized logging configuration for spot-optimizer.

This module provides a centralized logging setup with configurable log levels,
consistent formatting, and support for both console and file logging with rotation.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict, Any
from appdirs import user_log_dir


# Global configuration variables with environment variable support
DEFAULT_LOG_LEVEL = getattr(
    logging, os.environ.get("SPOT_OPTIMIZER_DEFAULT_LOG_LEVEL", "INFO"), logging.INFO
)
DEFAULT_FORMAT = os.environ.get(
    "SPOT_OPTIMIZER_DEFAULT_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
DEFAULT_DATE_FORMAT = os.environ.get(
    "SPOT_OPTIMIZER_DEFAULT_DATE_FORMAT", "%Y-%m-%d %H:%M:%S"
)


# Environment-based default configurations (can be overridden by environment variables)
def _get_development_config() -> Dict[str, Any]:
    """Get development configuration with environment variable overrides."""
    return {
        "level": getattr(
            logging,
            os.environ.get("SPOT_OPTIMIZER_DEV_LOG_LEVEL", "DEBUG"),
            logging.DEBUG,
        ),
        "format": os.environ.get(
            "SPOT_OPTIMIZER_DEV_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        ),
        "console_enabled": os.environ.get("SPOT_OPTIMIZER_DEV_CONSOLE", "true").lower()
        == "true",
        "file_enabled": os.environ.get("SPOT_OPTIMIZER_DEV_FILE", "true").lower()
        == "true",
        "max_bytes": int(
            os.environ.get("SPOT_OPTIMIZER_DEV_MAX_BYTES", str(10 * 1024 * 1024))
        ),  # 10MB
        "backup_count": int(os.environ.get("SPOT_OPTIMIZER_DEV_BACKUP_COUNT", "5")),
    }


def _get_production_config() -> Dict[str, Any]:
    """Get production configuration with environment variable overrides."""
    return {
        "level": getattr(
            logging,
            os.environ.get("SPOT_OPTIMIZER_PROD_LOG_LEVEL", "INFO"),
            logging.INFO,
        ),
        "format": os.environ.get(
            "SPOT_OPTIMIZER_PROD_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        ),
        "console_enabled": os.environ.get("SPOT_OPTIMIZER_PROD_CONSOLE", "true").lower()
        == "true",
        "file_enabled": os.environ.get("SPOT_OPTIMIZER_PROD_FILE", "true").lower()
        == "true",
        "max_bytes": int(
            os.environ.get("SPOT_OPTIMIZER_PROD_MAX_BYTES", str(50 * 1024 * 1024))
        ),  # 50MB
        "backup_count": int(os.environ.get("SPOT_OPTIMIZER_PROD_BACKUP_COUNT", "10")),
    }


def _get_testing_config() -> Dict[str, Any]:
    """Get testing configuration with environment variable overrides."""
    return {
        "level": getattr(
            logging,
            os.environ.get("SPOT_OPTIMIZER_TEST_LOG_LEVEL", "WARNING"),
            logging.WARNING,
        ),
        "format": os.environ.get(
            "SPOT_OPTIMIZER_TEST_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        ),
        "console_enabled": os.environ.get(
            "SPOT_OPTIMIZER_TEST_CONSOLE", "false"
        ).lower()
        == "true",
        "file_enabled": os.environ.get("SPOT_OPTIMIZER_TEST_FILE", "false").lower()
        == "true",
        "max_bytes": int(
            os.environ.get("SPOT_OPTIMIZER_TEST_MAX_BYTES", str(5 * 1024 * 1024))
        ),  # 5MB
        "backup_count": int(os.environ.get("SPOT_OPTIMIZER_TEST_BACKUP_COUNT", "3")),
    }


# Environment configurations getter
ENVIRONMENT_CONFIGS = {
    "development": _get_development_config,
    "production": _get_production_config,
    "testing": _get_testing_config,
}

# Global state variables
_configured = False
_log_dir: Optional[Path] = None


def get_log_directory() -> Path:
    """
    Get the log directory path in user data directory.

    Returns:
        Path: Path to the log directory
    """
    global _log_dir
    if _log_dir is None:
        app_name = os.environ.get("SPOT_OPTIMIZER_APP_NAME", "spot-optimizer")
        app_author = os.environ.get("SPOT_OPTIMIZER_APP_AUTHOR", "aws-samples")
        log_dir = user_log_dir(app_name, app_author)
        _log_dir = Path(log_dir)
        _log_dir.mkdir(parents=True, exist_ok=True)
    return _log_dir


def get_log_level_from_env() -> int:
    """
    Get log level from environment variables.

    Returns:
        int: Logging level
    """
    env_level = os.getenv("SPOT_OPTIMIZER_LOG_LEVEL", "INFO").upper()
    return getattr(logging, env_level, DEFAULT_LOG_LEVEL)


def get_environment() -> str:
    """
    Get current environment from environment variables.

    Returns:
        str: Environment name (development, production, testing)
    """
    return os.getenv("SPOT_OPTIMIZER_ENV", "production").lower()


def get_config_for_environment(environment: str = None) -> Dict[str, Any]:
    """
    Get configuration for specific environment.

    Args:
        environment: Environment name, if None uses current environment

    Returns:
        dict: Configuration dictionary
    """
    if environment is None:
        environment = get_environment()

    config_getter = ENVIRONMENT_CONFIGS.get(
        environment, ENVIRONMENT_CONFIGS["production"]
    )
    config = config_getter().copy()

    # Override with environment variables if available
    env_level = get_log_level_from_env()
    if env_level != DEFAULT_LOG_LEVEL:
        config["level"] = env_level

    # Override console/file settings from environment
    if os.getenv("SPOT_OPTIMIZER_LOG_CONSOLE") is not None:
        config["console_enabled"] = (
            os.getenv("SPOT_OPTIMIZER_LOG_CONSOLE").lower() == "true"
        )

    if os.getenv("SPOT_OPTIMIZER_LOG_FILE") is not None:
        config["file_enabled"] = os.getenv("SPOT_OPTIMIZER_LOG_FILE").lower() == "true"

    return config


def setup_logging(
    logger_name: str = "spot_optimizer",
    log_level: Optional[int] = None,
    log_format: Optional[str] = None,
    console_enabled: Optional[bool] = None,
    file_enabled: Optional[bool] = None,
    log_file: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    force_reconfigure: bool = False,
) -> logging.Logger:
    """
    Setup centralized logging configuration.

    Args:
        logger_name: Name of the logger (default: "spot_optimizer")
        log_level: Logging level (if None, uses environment config)
        log_format: Log format string (if None, uses environment config)
        console_enabled: Enable console logging (if None, uses environment config)
        file_enabled: Enable file logging (if None, uses environment config)
        log_file: Log file name (if None, uses default)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        force_reconfigure: Force reconfiguration even if already configured

    Returns:
        logging.Logger: Configured logger instance
    """
    global _configured

    # Avoid duplicate configuration unless forced
    if _configured and not force_reconfigure:
        return logging.getLogger(logger_name)

    # Get environment-based configuration
    env_config = get_config_for_environment()

    # Use provided parameters or fall back to environment config
    log_level = log_level if log_level is not None else env_config["level"]
    log_format = log_format if log_format is not None else env_config["format"]
    console_enabled = (
        console_enabled
        if console_enabled is not None
        else env_config["console_enabled"]
    )
    file_enabled = (
        file_enabled if file_enabled is not None else env_config["file_enabled"]
    )
    max_bytes = max_bytes if max_bytes is not None else env_config["max_bytes"]
    backup_count = (
        backup_count if backup_count is not None else env_config["backup_count"]
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(fmt=log_format, datefmt=DEFAULT_DATE_FORMAT)

    # Setup console handler
    if console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Setup file handler with rotation
    if file_enabled:
        log_dir = get_log_directory()
        log_file = log_file or f"{logger_name}.log"
        log_path = log_dir / log_file

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Mark as configured
    _configured = True

    # Get the specific logger
    logger = logging.getLogger(logger_name)

    # Log configuration info
    environment = get_environment()
    logger.info(f"Logging configured for environment: {environment}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Console logging: {'enabled' if console_enabled else 'disabled'}")
    logger.info(f"File logging: {'enabled' if file_enabled else 'disabled'}")
    if file_enabled:
        logger.info(f"Log directory: {get_log_directory()}")

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with centralized configuration.

    This function ensures that logging is configured before returning the logger.
    It's the recommended way to get loggers in the application.

    Args:
        name: Logger name (if None, uses the calling module's name)

    Returns:
        logging.Logger: Configured logger instance
    """
    global _configured

    # Auto-configure if not already done
    if not _configured:
        setup_logging()

    # Use provided name or determine from caller
    if name is None:
        import inspect

        frame = inspect.currentframe()
        try:
            # Get the caller's module name
            caller_frame = frame.f_back
            name = caller_frame.f_globals.get("__name__", "spot_optimizer")
        finally:
            del frame

    return logging.getLogger(name)


def reset_configuration():
    """
    Reset logging configuration for testing purposes.

    This function should only be used in tests.
    """
    global _configured, _log_dir

    _configured = False
    _log_dir = None

    # Clear all handlers from root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.WARNING)  # Reset to default


# Auto-configure logging when module is imported
# This ensures that logging is always configured in production
if not _configured:
    setup_logging()

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


class LoggingConfig:
    """Centralized logging configuration manager."""

    # Default configuration
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Environment-based configurations
    ENVIRONMENT_CONFIGS = {
        "development": {
            "level": logging.DEBUG,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            "console_enabled": True,
            "file_enabled": True,
            "max_bytes": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5,
        },
        "production": {
            "level": logging.INFO,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "console_enabled": True,
            "file_enabled": True,
            "max_bytes": 50 * 1024 * 1024,  # 50MB
            "backup_count": 10,
        },
        "testing": {
            "level": logging.WARNING,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "console_enabled": False,
            "file_enabled": False,
            "max_bytes": 5 * 1024 * 1024,  # 5MB
            "backup_count": 3,
        },
    }

    _configured = False
    _log_dir: Optional[Path] = None

    @classmethod
    def get_log_directory(cls) -> Path:
        """
        Get the log directory path in user data directory.

        Returns:
            Path: Path to the log directory
        """
        if cls._log_dir is None:
            app_name = "spot-optimizer"
            app_author = "aws-samples"
            log_dir = user_log_dir(app_name, app_author)
            cls._log_dir = Path(log_dir)
            cls._log_dir.mkdir(parents=True, exist_ok=True)
        return cls._log_dir

    @classmethod
    def get_log_level_from_env(cls) -> int:
        """
        Get log level from environment variables.

        Returns:
            int: Logging level
        """
        env_level = os.getenv("SPOT_OPTIMIZER_LOG_LEVEL", "INFO").upper()
        return getattr(logging, env_level, cls.DEFAULT_LOG_LEVEL)

    @classmethod
    def get_environment(cls) -> str:
        """
        Get current environment from environment variables.

        Returns:
            str: Environment name (development, production, testing)
        """
        return os.getenv("SPOT_OPTIMIZER_ENV", "production").lower()

    @classmethod
    def get_config_for_environment(cls, environment: str = None) -> Dict[str, Any]:
        """
        Get configuration for specific environment.

        Args:
            environment: Environment name, if None uses current environment

        Returns:
            dict: Configuration dictionary
        """
        if environment is None:
            environment = cls.get_environment()

        config = cls.ENVIRONMENT_CONFIGS.get(
            environment, cls.ENVIRONMENT_CONFIGS["production"]
        ).copy()

        # Override with environment variables if available
        env_level = cls.get_log_level_from_env()
        if env_level != cls.DEFAULT_LOG_LEVEL:
            config["level"] = env_level

        # Override console/file settings from environment
        if os.getenv("SPOT_OPTIMIZER_LOG_CONSOLE") is not None:
            config["console_enabled"] = (
                os.getenv("SPOT_OPTIMIZER_LOG_CONSOLE").lower() == "true"
            )

        if os.getenv("SPOT_OPTIMIZER_LOG_FILE") is not None:
            config["file_enabled"] = (
                os.getenv("SPOT_OPTIMIZER_LOG_FILE").lower() == "true"
            )

        return config

    @classmethod
    def setup_logging(
        cls,
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
        # Avoid duplicate configuration unless forced
        if cls._configured and not force_reconfigure:
            return logging.getLogger(logger_name)

        # Get environment-based configuration
        env_config = cls.get_config_for_environment()

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
        formatter = logging.Formatter(fmt=log_format, datefmt=cls.DEFAULT_DATE_FORMAT)

        # Setup console handler
        if console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # Setup file handler with rotation
        if file_enabled:
            log_dir = cls.get_log_directory()
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
        cls._configured = True

        # Get the specific logger
        logger = logging.getLogger(logger_name)

        # Log configuration info
        environment = cls.get_environment()
        logger.info(f"Logging configured for environment: {environment}")
        logger.info(f"Log level: {logging.getLevelName(log_level)}")
        logger.info(f"Console logging: {'enabled' if console_enabled else 'disabled'}")
        logger.info(f"File logging: {'enabled' if file_enabled else 'disabled'}")
        if file_enabled:
            logger.info(f"Log directory: {cls.get_log_directory()}")

        return logger

    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """
        Get a logger instance with centralized configuration.

        This method ensures that logging is configured before returning the logger.
        It's the recommended way to get loggers in the application.

        Args:
            name: Logger name (if None, uses the calling module's name)

        Returns:
            logging.Logger: Configured logger instance
        """
        # Auto-configure if not already done
        if not cls._configured:
            cls.setup_logging()

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

    @classmethod
    def reset_configuration(cls):
        """
        Reset logging configuration for testing purposes.

        This method should only be used in tests.
        """
        cls._configured = False
        cls._log_dir = None

        # Clear all handlers from root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)  # Reset to default


# Convenience functions for common usage patterns
def setup_logging(**kwargs) -> logging.Logger:
    """
    Setup centralized logging configuration.

    This is a convenience function that wraps LoggingConfig.setup_logging().

    Args:
        **kwargs: Arguments to pass to LoggingConfig.setup_logging()

    Returns:
        logging.Logger: Configured logger instance
    """
    return LoggingConfig.setup_logging(**kwargs)


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with centralized configuration.

    This is a convenience function that wraps LoggingConfig.get_logger().

    Args:
        name: Logger name (if None, uses the calling module's name)

    Returns:
        logging.Logger: Configured logger instance
    """
    return LoggingConfig.get_logger(name)


# Auto-configure logging when module is imported
# This ensures that logging is always configured in production
if not LoggingConfig._configured:
    setup_logging()

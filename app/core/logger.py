"""
Centralized logging configuration for the Deribit Tracker application.

Provides a singleton logger factory with configurable log levels,
multiple handlers (console, file), and consistent formatting across
all application modules.
"""

import logging
import sys
from typing import ClassVar


class AppLogger:
    """
    Singleton logger factory for consistent application-wide logging.

    Provides centralized logging configuration with support for both
    console and file output, log rotation, and dynamic log level
    configuration based on application settings.
    """

    _initialized: ClassVar[bool] = False
    _date_format: ClassVar[str] = "%Y-%m-%d %H:%M:%S"
    _log_format: ClassVar[str] = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create application logger instance.

        Args:
            name: Logger name, typically __name__ of calling module.

        Returns:
            Configured logger instance with appropriate handlers.
        """
        logger = logging.getLogger(name)

        if not cls._initialized:
            cls._configure_root_logger()
            cls._initialized = True

        return logger

    @classmethod
    def _configure_root_logger(cls) -> None:
        """Configure root logger with console and file handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

        formatter = logging.Formatter(
            fmt=cls._log_format,
            datefmt=cls._date_format,
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

    @classmethod
    def set_level(
        cls,
        level: int | str,
        logger_name: str | None = None,
    ) -> None:
        """
        Set logging level for specific or all application loggers.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            logger_name: Specific logger name to configure,
                         or None for root logger.
        """
        logger = logging.getLogger(logger_name)

        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)

        logger.setLevel(level)

        if logger_name is None:
            for handler in logger.handlers:
                handler.setLevel(level)

    @classmethod
    def disable_logger(cls, logger_name: str) -> None:
        """
        Disable logging for a specific logger.

        Args:
            logger_name: Name of logger to disable.
        """
        logging.getLogger(logger_name).disabled = True


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Convenience function to get application logger.

    Args:
        name: Logger name, typically __name__ of calling module.

    Returns:
        Configured logger instance.
    """
    return AppLogger.get_logger(name)

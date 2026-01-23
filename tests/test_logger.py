"""
Unit tests for application logging system.

Tests logger configuration, log level management, and logging behavior
across different scenarios.
"""

import logging
from unittest.mock import Mock, patch

from app.core.logger import AppLogger, get_logger


class TestAppLogger:
    """Test AppLogger singleton and configuration."""

    def setup_method(self):
        """Reset logger state before each test."""
        AppLogger._initialized = False
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        root_logger.setLevel(logging.WARNING)

    def test_singleton_initialization(self):
        """Test logger is initialized only once."""
        logger1 = AppLogger.get_logger("test.module1")
        logger2 = AppLogger.get_logger("test.module2")

        assert AppLogger._initialized is True
        assert logger1.name == "test.module1"
        assert logger2.name == "test.module2"

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 1

    def test_logger_hierarchy(self):
        """Test logger hierarchy and propagation."""
        parent_logger = AppLogger.get_logger("parent")
        child_logger = AppLogger.get_logger("parent.child")

        assert child_logger.parent is parent_logger
        assert child_logger.propagate is True

    def test_get_logger_convenience_function(self):
        """Test get_logger() convenience function."""
        logger1 = get_logger("test.module")
        logger2 = AppLogger.get_logger("test.module")

        assert logger1 is logger2
        assert logger1.name == "test.module"

    def test_log_level_setting(self):
        """Test dynamic log level configuration."""
        test_logger = AppLogger.get_logger("test.level")
        test_logger.setLevel(logging.INFO)

        import io

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)
        test_logger.propagate = False

        test_logger.debug("This should not appear")
        test_logger.info("This should appear")

        log_output = stream.getvalue()
        assert "This should not appear" not in log_output
        assert "This should appear" in log_output

        test_logger.removeHandler(handler)

    def test_logger_specific_level_setting(self):
        """Test setting log level for specific logger only."""
        logger1 = AppLogger.get_logger("test.specific1")
        logger2 = AppLogger.get_logger("test.specific2")

        import io

        stream1 = io.StringIO()
        stream2 = io.StringIO()

        handler1 = logging.StreamHandler(stream1)
        handler2 = logging.StreamHandler(stream2)

        for handler in [handler1, handler2]:
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(
                logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            )

        logger1.addHandler(handler1)
        logger2.addHandler(handler2)
        logger1.propagate = False
        logger2.propagate = False

        logger1.setLevel(logging.ERROR)
        logger2.setLevel(logging.DEBUG)

        logger1.info("Logger1 info - should not appear")
        logger1.error("Logger1 error - should appear")
        logger2.debug("Logger2 debug - should appear")
        logger2.info("Logger2 info - should appear")

        output1 = stream1.getvalue()
        output2 = stream2.getvalue()

        assert "Logger1 info - should not appear" not in output1
        assert "Logger1 error - should appear" in output1
        assert "Logger2 debug - should appear" in output2
        assert "Logger2 info - should appear" in output2

        logger1.removeHandler(handler1)
        logger2.removeHandler(handler2)

    def test_disable_logger(self):
        """Test disabling specific loggers."""
        test_logger = AppLogger.get_logger("test.disabled")
        other_logger = AppLogger.get_logger("test.enabled")

        import io

        stream1 = io.StringIO()
        stream2 = io.StringIO()

        handler1 = logging.StreamHandler(stream1)
        handler2 = logging.StreamHandler(stream2)

        for handler in [handler1, handler2]:
            handler.setLevel(logging.INFO)
            handler.setFormatter(
                logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            )

        test_logger.addHandler(handler1)
        other_logger.addHandler(handler2)
        test_logger.propagate = False
        other_logger.propagate = False

        AppLogger.disable_logger("test.disabled")

        test_logger.info("This should not appear")
        other_logger.info("This should appear")

        output1 = stream1.getvalue()
        output2 = stream2.getvalue()

        assert "This should not appear" not in output1
        assert "This should appear" in output2

        test_logger.removeHandler(handler1)
        other_logger.removeHandler(handler2)

    def test_log_format(self):
        """Test log message formatting."""
        test_logger = AppLogger.get_logger("test.format")

        import io

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)
        test_logger.propagate = False

        test_logger.info("Test message with number: %d", 42)

        log_output = stream.getvalue().strip()

        assert "test.format" in log_output
        assert "INFO" in log_output
        assert "Test message with number: 42" in log_output
        assert "20" in log_output
        assert "- test.format - INFO -" in log_output

        test_logger.removeHandler(handler)

    def test_multiple_get_logger_calls(self):
        """Test that multiple get_logger calls return same instance."""
        logger1 = AppLogger.get_logger("test.duplicate")
        logger2 = AppLogger.get_logger("test.duplicate")
        logger3 = get_logger("test.duplicate")

        assert logger1 is logger2
        assert logger1 is logger3

    def test_root_logger_configuration(self):
        """Test root logger is properly configured."""
        AppLogger.get_logger("test.root")

        root_logger = logging.getLogger()

        assert len(root_logger.handlers) == 1

        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.level == logging.INFO

    def test_file_handler_not_added_by_default(self):
        """Test file handler is not added without debug mode."""
        AppLogger.get_logger("test.file")

        root_logger = logging.getLogger()
        file_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(
                h,
                logging.handlers.RotatingFileHandler,  # type: ignore
            )
        ]

        assert len(file_handlers) == 0

    def test_exception_logging(self):
        """Test logging of exceptions with traceback."""
        test_logger = AppLogger.get_logger("test.exception")

        import io

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)
        test_logger.propagate = False

        try:
            raise ValueError("Test exception")
        except ValueError:
            test_logger.exception("An error occurred")

        log_output = stream.getvalue()
        assert "An error occurred" in log_output
        assert "ValueError" in log_output
        assert "Test exception" in log_output

        test_logger.removeHandler(handler)

    def test_log_level_string_conversion(self):
        """Test string to log level conversion."""
        for level_name in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            AppLogger.set_level(level_name)
            root_logger = logging.getLogger()
            expected_level = getattr(logging, level_name)
            assert root_logger.level == expected_level

        AppLogger.set_level("INVALID_LEVEL")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO


def test_logger_in_different_modules():
    """Test that loggers in different modules work correctly."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2.submodule")
    logger3 = get_logger("module3")

    assert logger1.name == "module1"
    assert logger2.name == "module2.submodule"
    assert logger3.name == "module3"

    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 1


@patch("app.core.logger.Path.mkdir")
@patch("logging.getLogger")
def test_file_handler_creation_error(mock_get_logger, mock_mkdir):
    """Test error handling when file handler creation fails."""
    mock_mkdir.side_effect = PermissionError("Permission denied")

    mock_logger = Mock(spec=logging.Logger)
    mock_logger.warning = Mock()
    mock_logger.addHandler = Mock()
    mock_get_logger.return_value = mock_logger

    formatter = logging.Formatter()

    AppLogger._add_file_handler(mock_logger, formatter)

    mock_logger.warning.assert_called_once_with(
        "Could not create file handler: %s",
        mock_mkdir.side_effect,
    )

    mock_logger.addHandler.assert_not_called()

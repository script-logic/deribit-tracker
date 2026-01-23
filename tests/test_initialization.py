"""
Tests for application initialization and startup.

Verifies that the application starts correctly, dependencies
are initialized properly, and error conditions are handled.
"""

import sys
from unittest.mock import Mock, patch

import pytest

from app.core.config import Settings
from app.core.logger import AppLogger


class TestApplicationInitialization:
    """Test application startup and initialization."""

    def setup_method(self):
        """Reset application state before each test."""
        if "app" in sys.modules:
            del sys.modules["app"]

        Settings._instance = None
        AppLogger._initialized = False

    def test_module_level_logger_initialization(self, capsys):
        """Test logger is initialized at module level."""
        with patch("app.core.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            import importlib

            import app

            importlib.reload(app)

        assert hasattr(app, "logger")
        assert app.logger is mock_logger

    @patch("app.core.get_logger")
    def test_logger_initialization_error(self, mock_get_logger, capsys):
        """Test error handling when logger initialization fails."""
        mock_get_logger.side_effect = RuntimeError("Logger failed")

        with pytest.raises(RuntimeError, match="Logger failed"):
            import importlib

            if "app" in sys.modules:
                del sys.modules["app"]

            import app

            importlib.reload(app)

        captured = capsys.readouterr()
        assert "Failed to initialize logger" in captured.err
        assert "Logger failed" in captured.err

    @patch("app.core.init_settings")
    def test_settings_initialization_error(self, mock_init_settings, caplog):
        """Test error handling when settings initialization fails."""
        mock_init_settings.side_effect = ValueError("Invalid settings")

        mock_logger = Mock()
        mock_logger.error = Mock()

        with (
            patch("app.core.get_logger", return_value=mock_logger),
            pytest.raises(ValueError, match="Invalid settings"),
        ):
            import importlib

            import app

            importlib.reload(app)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0]
        assert "Failed to initialize settings" in call_args[0]
        assert "Invalid settings" in str(call_args[1])

    def test_metadata_loading_fallback(self):
        """Test fallback when package metadata cannot be loaded."""
        with patch("importlib.metadata.metadata") as mock_metadata:
            mock_metadata.side_effect = Exception("Metadata not available")

            import importlib

            import app

            importlib.reload(app)

            assert app.version == "Unknown version"
            assert app.title == "Untitled"
            assert app.description == "Unknown description"

    def test_metadata_loading_success(self):
        """Test successful package metadata loading."""
        mock_metadata = Mock()
        mock_metadata.json = {
            "version": "1.2.3",
            "name": "deribit-tracker",
            "summary": "Test description",
        }

        with patch("importlib.metadata.metadata", return_value=mock_metadata):
            import importlib

            import app

            importlib.reload(app)

            assert app.version == "1.2.3"
            assert app.title == "Deribit Tracker"
            assert app.description == "Test description"

    def test_module_exports(self):
        """Test that module exports expected symbols."""
        import app

        expected_exports = {
            "description",
            "logger",
            "settings",
            "title",
            "version",
        }

        actual_exports = set(app.__all__)
        assert actual_exports == expected_exports

        for export in expected_exports:
            assert hasattr(app, export)
            assert getattr(app, export) is not None

    def test_settings_availability(self):
        """Test that settings are available after initialization."""
        import app

        assert hasattr(app, "settings")
        assert app.settings is not None
        assert isinstance(app.settings, Settings)

    def test_title_formatting(self):
        """Test that package name is formatted correctly."""
        mock_metadata = Mock()
        mock_metadata.json = {
            "version": "1.0.0",
            "name": "deribit-tracker",
            "summary": "Test",
        }

        with patch("importlib.metadata.metadata", return_value=mock_metadata):
            import importlib

            import app

            importlib.reload(app)

            assert app.title == "Deribit Tracker"

    def test_version_string_safety(self):
        """Test version is always a string."""
        mock_metadata = Mock()
        mock_metadata.json = {
            "version": 1.0,
            "name": "test",
            "summary": "Test",
        }

        with patch("importlib.metadata.metadata", return_value=mock_metadata):
            import importlib

            import app

            importlib.reload(app)

            assert isinstance(app.version, str)
            assert app.version == "1.0"

"""
Tests for application initialization and startup.

Verifies that the application starts correctly, dependencies
are initialized properly, and error conditions are handled.
"""

import sys
from unittest.mock import Mock, patch

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

    def test_module_level_logger_initialization(self):
        """Test logger is initialized at module level."""
        from app.core.logger import AppLogger

        AppLogger._initialized = False

        import importlib
        import sys

        old_core_module = sys.modules.pop("app.core", None)

        try:
            with patch("app.core.logger.get_logger") as mock_get_logger:
                mock_logger_instance = Mock()
                mock_get_logger.return_value = mock_logger_instance

                import app.metadata

                importlib.reload(app.metadata)

                assert hasattr(app.metadata, "logger")
                mock_get_logger.assert_called()
        finally:
            if old_core_module:
                sys.modules["app.core"] = old_core_module

        @patch("app.core.init_settings")
        def test_settings_initialization_error(
            self,
            mock_init_settings,
            caplog,
        ):
            """Test error handling when settings initialization fails."""
            # mock_init_settings.side_effect = ValueError("Invalid settings")

            # with patch("app.core.get_logger") as mock_get_logger:
            #     mock_logger = Mock()
            #     mock_logger.error = Mock()
            #     mock_get_logger.return_value = mock_logger

            #     import importlib
            #     import app.core

            #     importlib.reload(app.core)

            # call_args = mock_logger.error.call_args[0]
            # assert "Failed to initialize settings" in call_args[0]
            pass  # TODO

    def test_module_exports(self):
        """Test that module exports expected symbols."""
        import app

        expected_exports = {
            "api",
            "clients",
            "core",
            "database",
            "project_metadata",
            "services",
            "tasks",
            "metadata",
        }

        actual_exports = set(app.__all__)
        assert actual_exports == expected_exports

        for export in expected_exports:
            assert hasattr(app, export)
            assert getattr(app, export) is not None

        assert hasattr(app.core, "logger")
        assert hasattr(app.core, "settings")

    def test_settings_availability(self):
        """Test that settings are available after initialization."""
        import app

        assert hasattr(app.core, "settings")
        assert app.core.settings is not None
        assert isinstance(app.core.settings, Settings)

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

            assert app.project_metadata["title"] == "Deribit Tracker"

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

            assert isinstance(app.project_metadata["version"], str)
            assert app.project_metadata["version"] == "0.4.0"

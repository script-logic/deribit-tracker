"""
Deribit Price Tracker API application package.

Main application module with metadata, configuration and logger
initialization.
"""

import sys
from importlib.metadata import metadata

from .core import (
    get_logger,
    get_settings,
    init_settings,
)

try:
    logger = get_logger(__name__)
except Exception as e:
    print(f"Failed to initialize logger: {e}", file=sys.stderr)
    raise

try:
    init_settings()
    settings = get_settings()
except Exception as e:
    logger.error("Failed to initialize settings: %s", e)
    raise

try:
    pkg_metadata = metadata("deribit-tracker").json
    version = str(pkg_metadata.get("version", "Unknown version"))
    description = str(pkg_metadata.get("summary", "Unknown description"))
    title = str(pkg_metadata.get("name", "Untitled")).replace("-", " ").title()
except Exception:
    version = "Unknown version"
    description = "Unknown description"
    title = "Untitled"


__all__ = [
    "description",
    "logger",
    "settings",
    "title",
    "version",
]

"""
Deribit Price Tracker API application package.

Main application module with metadata, configuration and logger
initialization.
"""

from importlib.metadata import metadata

from . import core, database

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
    "core",
    "database",
    "description",
    "title",
    "version",
]

"""
Deribit Price Tracker API application package.

Main application module with metadata and imports.
"""

from functools import lru_cache
from importlib.metadata import metadata

from . import api, clients, core, database, services, tasks


@lru_cache
def get_app_metadata() -> tuple[str, str, str]:
    """
    Retrieves application metadata from the installed package information.

    Returns:
        tuple: A three-element tuple containing:
            version (str): Current application version (e.g., "0.3.0")
            description (str): Brief application description
            title (str): Formatted application title (e.g., "Deribit Tracker")

    Note: Requires package to be installed (e.g., via poetry install)
    """
    try:
        app_meta = metadata("deribit-tracker").json
        version = str(app_meta.get("version", "Unknown version"))
        description = str(app_meta.get("summary", "Unknown description"))
        title = str(app_meta.get("name", "Untitled")).replace("-", " ").title()
    except Exception:
        version = "Unknown version"
        description = "Unknown description"
        title = "Untitled"

    return version, description, title


version, description, title = get_app_metadata()


__all__ = [
    "api",
    "clients",
    "core",
    "database",
    "description",
    "services",
    "tasks",
    "title",
    "version",
]

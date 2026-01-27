from pathlib import Path

import toml

from app.core.logger import get_logger

logger = get_logger(__name__)


def get_project_metadata() -> dict[str, str]:
    """
    Retrieves application metadata from the installed package information.

    Returns:
        dict:
            version (str): Current application version (e.g., "0.4.0")
            description (str): Brief application description
            title (str): Formatted application title (e.g., "Deribit Tracker")
    """
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    try:
        data = toml.load(pyproject_path)

        project_section = data.get("project", {})

        return {
            "version": project_section.get("version", "Unknown"),
            "description": project_section.get("description", ""),
            "title": project_section
            .get("name", "Unknown")
            .replace("-", " ")
            .title(),
        }
    except Exception as e:
        logger.warning(f"Warning: Could not read pyproject.toml: {e}")

    return {
        "title": "Unknown",
        "version": "Unknown",
        "description": "",
    }


project_metadata: dict[str, str] = get_project_metadata()

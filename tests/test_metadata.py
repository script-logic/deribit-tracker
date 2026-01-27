from app.metadata import project_metadata


def test_package_metadata_loaded():
    assert project_metadata["version"] is not None
    assert project_metadata["title"] is not None
    assert project_metadata["description"] is not None
    assert len(project_metadata["version"]) > 0
    assert len(project_metadata["title"]) > 0


def test_version_matches_pyproject():
    assert project_metadata["version"] == "0.4.0"


def test_title_formatting():
    assert "-" not in project_metadata["title"]
    assert project_metadata["title"][0].isupper()

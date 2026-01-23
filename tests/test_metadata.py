from importlib.metadata import metadata

from app import description, title, version


def test_package_metadata_loaded():
    assert version is not None
    assert title is not None
    assert description is not None
    assert len(version) > 0
    assert len(title) > 0


def test_version_matches_pyproject():
    pkg_metadata = metadata("deribit-tracker").json
    expected_version = pkg_metadata.get("version", "0.1.0")
    assert version == expected_version


def test_title_formatting():
    assert "-" not in title
    assert title[0].isupper()

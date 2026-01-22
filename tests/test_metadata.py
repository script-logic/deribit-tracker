from importlib.metadata import metadata

from app import __description__, __title__, __version__


def test_package_metadata_loaded():
    assert __version__ is not None
    assert __title__ is not None
    assert __description__ is not None
    assert len(__version__) > 0
    assert len(__title__) > 0


def test_version_matches_pyproject():
    pkg_metadata = metadata("deribit-tracker").json
    expected_version = pkg_metadata.get("version", "0.1.0")
    assert __version__ == expected_version


def test_title_formatting():
    assert "-" not in __title__
    assert __title__[0].isupper()

from importlib.metadata import metadata

pkg_metadata = metadata("deribit-tracker").json
__version__ = str(pkg_metadata.get("version", "Unversioned"))
__description__ = str(pkg_metadata.get("summary", "No description"))
__title__ = str(pkg_metadata.get("name", "Unnamed")).replace("-", " ").title()

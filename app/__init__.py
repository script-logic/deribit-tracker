from importlib.metadata import metadata

pkg_metadata = metadata("deribit-tracker").json
version = str(pkg_metadata.get("version", "Unversioned"))
description = str(pkg_metadata.get("summary", "No description"))
title = str(pkg_metadata.get("name", "Unnamed")).replace("-", " ").title()

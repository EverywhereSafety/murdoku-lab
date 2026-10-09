"""Packaged defaults and checkout-local files used by optional tools."""

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULTS = PACKAGE_ROOT / "resources"
_checkout = PACKAGE_ROOT.parent
PROJECT_ROOT = Path(
    os.environ.get(
        "MURDOKU_PROJECT_ROOT",
        _checkout if (_checkout / "package.json").is_file() else Path.cwd(),
    )
).resolve()

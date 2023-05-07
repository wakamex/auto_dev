"""
Constants for the auto_dev package.
"""

import os
from pathlib import Path

DEFAULT_ENCODING = "utf-8"
# package directory
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PYLAMA_CONFIG = Path(PACKAGE_DIR) / "data" / "pylama.ini"
AUTONOMY_PACKAGES_FILE = "packages/packages.json"

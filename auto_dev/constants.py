"""
Constants for the auto_dev package.
"""

import os
from pathlib import Path

DEFAULT_ENCODING = "utf-8"
DEFAULT_TIMEOUT = 10
# package directory
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PYLAMA_CONFIG = Path(PACKAGE_DIR) / "data" / "pylama.ini"
AUTONOMY_PACKAGES_FILE = "packages/packages.json"
AUTO_DEV_FOLDER = os.path.join(os.path.dirname(__file__))
PLUGIN_FOLDER = os.path.join(AUTO_DEV_FOLDER, "commands")
TEMPLATE_FOLDER = os.path.join(AUTO_DEV_FOLDER, "data", "repo", "templates")

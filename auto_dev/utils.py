"""
Utilities for auto_dev.
"""
import json
import logging
import os
import shutil
from contextlib import contextmanager
from functools import reduce
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from rich.logging import RichHandler

from .constants import AUTONOMY_PACKAGES_FILE, DEFAULT_ENCODING


def get_logger(name=__name__, log_level="INFO"):
    """Get the logger."""
    msg_format = "%(message)s"
    handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
    )
    logging.basicConfig(level="NOTSET", format=msg_format, datefmt="[%X]", handlers=[handler])

    log = logging.getLogger(name)
    log.setLevel(log_level)
    return log


def get_packages():
    """Get the packages file."""
    with open(AUTONOMY_PACKAGES_FILE, "r", encoding=DEFAULT_ENCODING) as file:
        packages = json.load(file)
    dev_packages = packages["dev"]
    results = []
    for package in dev_packages:
        component_type, author, component_name, _ = package.split("/")
        package_path = Path(f"packages/{author}/{component_type}s/{component_name}")
        if not package_path.exists():
            raise FileNotFoundError(f"Package {package} does not exist")
        results.append(package_path)
    return results


def get_paths(path=Optional[str]):
    """Get the paths."""
    if not path and not Path(AUTONOMY_PACKAGES_FILE).exists():
        raise FileNotFoundError("No path was provided and no default packages file found")
    packages = get_packages() if not path else [path]
    return reduce(lambda x, y: x + y, [glob(f"{package}/**/*py", recursive=True) for package in packages])


@contextmanager
def isolated_filesystem(copy_cwd: bool = False):
    """
    Context manager to create an isolated file system.
    And to navigate to it and then to clean it up.
    """
    original_path = Path.cwd()
    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        if copy_cwd:
            # we copy the content of the original directory into the temporary one
            for file_name in os.listdir(original_path):
                if file_name == "__pycache__":
                    continue
                file_path = Path(original_path, file_name)
                if file_path.is_file():
                    shutil.copy(file_path, temp_dir)
                elif file_path.is_dir():
                    shutil.copytree(file_path, Path(temp_dir, file_name))
        yield str(Path(temp_dir))
    os.chdir(original_path)

"""
We test the functions from utils
"""

from pathlib import Path

from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.utils import get_logger, get_packages, has_package_code_changed


def test_get_logger():
    """Test get_logger."""
    log = get_logger()
    assert log.level == 20


def test_get_packages():
    """Test get_packages."""
    packages = get_packages()
    assert len(packages) == 0


def test_has_package_code_changed_true(test_filesystem):
    """
    Test has_package_code_changed.
    """
    with open(Path(test_filesystem) / Path("packages/test_file.txt"), "w", encoding=DEFAULT_ENCODING) as file:
        file.write("test")
    assert has_package_code_changed(Path("packages")) is True


def test_has_package_code_changed_false(test_filesystem):
    """
    Test has_package_code_changed.
    """
    assert has_package_code_changed(Path(test_filesystem) / Path("packages")) is False

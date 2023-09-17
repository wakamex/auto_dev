"""
We test the functions from utils
"""

import json
import shutil
from pathlib import Path

import pytest

from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.utils import get_logger, get_packages, get_paths, has_package_code_changed

TEST_PACKAGES_JSON = {
    "packages/packages.json": """
{
    "dev": {
        "agent/eightballer/tmp/aea-config.yaml": "bafybeiaa3jynk3bx4uged6wye7pddkpbyr2t7avzze475vkyu2bbjeddrm"
    },
    "third_party": {
    }
}
"""
}

TEST_PACKAGE_FILE = {
    "packages/eightballer/agents/tmp/aea-config.yaml": """
agent_name: tmp
author: eightballer
version: 0.1.0
license: Apache-2.0
description: ''
aea_version: '>=1.35.0, <2.0.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- open_aea/signing:1.0.0:bafybeibqlfmikg5hk4phzak6gqzhpkt6akckx7xppbp53mvwt6r73h7tk4
skills: []
default_connection: null
default_ledger: ethereum
required_ledgers:
- ethereum
default_routing: {}
connection_private_key_paths: {}
private_key_paths: {}
logging_config:
  disable_existing_loggers: false
  version: 1
dependencies:
  open-aea-ledger-ethereum: {}
"""
}


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
    assert has_package_code_changed(Path("packages"))


def test_has_package_code_changed_false(test_filesystem):
    """
    Test has_package_code_changed.
    """
    assert not has_package_code_changed(Path(test_filesystem) / Path("packages"))


@pytest.fixture
def autonomy_fs(test_filesystem):
    """
    Test get_paths.
    """
    Path(list(TEST_PACKAGES_JSON.keys()).pop())
    for key, value in TEST_PACKAGES_JSON.items():
        key_path = Path(test_filesystem) / Path(key)
        if key_path.exists():
            shutil.rmtree(key_path, ignore_errors=True)
        if not key_path.parent.exists():
            key_path.parent.mkdir(parents=True)
        with open(key_path, "w", encoding=DEFAULT_ENCODING) as path:
            path.write(value)

    for data_file in [
        TEST_PACKAGE_FILE,
    ]:
        for file_name, data in data_file.items():
            file_path = Path(test_filesystem) / Path(file_name)
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True)
            with open(file_path, "w", encoding=DEFAULT_ENCODING) as path:
                path.write(json.dumps(data))
    yield test_filesystem


def test_get_paths_changed_only(test_filesystem):
    """
    Test get_paths.
    """
    assert test_filesystem == str(Path.cwd())
    assert len(get_paths(changed_only=True)) == 0


def test_get_paths(test_filesystem):
    """
    Test get_paths.
    """
    assert test_filesystem == str(Path.cwd())
    assert len(get_paths()) == 0

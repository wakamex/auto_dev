"""
Conftest for testing command-line interfaces.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def isolated_filesystem():
    """Fixture for invoking command-line interfaces."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = f"{tmpdir}/dir"
        shutil.copytree(Path(cwd), test_dir)
        os.chdir(test_dir)
        yield test_dir
    os.chdir(cwd)

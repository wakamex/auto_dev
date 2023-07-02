"""
Conftest for testing command-line interfaces.
"""

import pytest

from auto_dev.utils import isolated_filesystem


@pytest.fixture
def test_filesystem():
    """Fixture for invoking command-line interfaces."""
    with isolated_filesystem(copy_cwd=True) as directory:
        yield directory

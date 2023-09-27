"""
Conftest for testing command-line interfaces.
"""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from auto_dev.cli_executor import CommandExecutor
from auto_dev.utils import isolated_filesystem


@pytest.fixture
def runner():
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def test_filesystem():
    """Fixture for invoking command-line interfaces."""
    with isolated_filesystem(copy_cwd=True) as directory:
        yield directory


@pytest.fixture
def test_clean_filesystem():
    """Fixture for invoking command-line interfaces."""
    with isolated_filesystem() as directory:
        yield directory


@pytest.fixture
def dummy_agent_tim(test_clean_filesystem) -> Path:
    """Fixture for dummy agent tim."""
    assert Path.cwd() == Path(test_clean_filesystem)

    command = CommandExecutor(["aea", "create", "tim"])
    result = command.execute(verbose=True)
    if not result:
        raise ValueError("Failed to create dummy agent tim")

    os.chdir(str(Path.cwd() / "tim"))
    return Path.cwd()

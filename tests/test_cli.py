"""
Tests for the click cli.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from auto_dev.cli import cli


@pytest.fixture
def runner():
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


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


def test_lint_fails(runner, isolated_filesystem):
    """Test the lint command fails with no packages."""
    assert os.getcwd() == isolated_filesystem
    result = runner.invoke(cli, ["lint"])
    assert result.exit_code == 1, result.output
    assert "Unable to get packages" in result.output, result.output


def test_lints_self(runner, isolated_filesystem):
    """Test the lint command works with the current package."""
    assert os.getcwd() == isolated_filesystem
    result = runner.invoke(cli, ["lint", "-p", "."])
    assert result.exit_code == 0, result.output


def test_formats_self(runner, isolated_filesystem):
    """Test the format command works with the current package."""
    assert os.getcwd() == isolated_filesystem
    result = runner.invoke(cli, ["fmt", "-p", "."])
    assert result.exit_code == 0, result.output

"""
Tests for the click cli.
"""

import os

import pytest
from click.testing import CliRunner

from auto_dev.cli import cli


@pytest.fixture
def runner():
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_lint_fails(runner, test_filesystem):
    """Test the lint command fails with no packages."""
    assert os.getcwd() == test_filesystem
    result = runner.invoke(cli, ["lint"])
    assert result.exit_code == 1, result.output
    assert result.exception is not None
    assert isinstance(result.exception, FileNotFoundError)


def test_lints_self(runner, test_filesystem):
    """Test the lint command works with the current package."""
    assert os.getcwd() == test_filesystem
    result = runner.invoke(cli, ["lint", "-p", "."])
    assert result.exit_code == 0, result.output


def test_formats_self(runner, test_filesystem):
    """Test the format command works with the current package."""
    assert os.getcwd() == test_filesystem
    result = runner.invoke(cli, ["fmt", "-p", "."])
    assert result.exit_code == 0, result.output

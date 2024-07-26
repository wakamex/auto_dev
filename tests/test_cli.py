"""
Tests for the click cli.
"""

import os

from auto_dev.cli import cli


def test_lint_fails(cli_runner, test_filesystem):
    """Test the lint command fails with no packages."""
    assert os.getcwd() == test_filesystem
    result = cli_runner.invoke(cli, ["lint", "-p", "packages/fake"])
    assert result.exit_code == 2, result.output
    assert result.exception is not None
    assert isinstance(SystemExit(2), type(result.exception))


def test_lints_self(cli_runner, test_filesystem):
    """Test the lint command works with the current package."""
    assert os.getcwd() == test_filesystem
    result = cli_runner.invoke(cli, ["-v", "lint", "-p", "."])
    assert result.exit_code == 0, result.output


def test_formats_self(cli_runner, test_filesystem):
    """Test the format command works with the current package."""
    assert os.getcwd() == test_filesystem
    result = cli_runner.invoke(cli, ["-v", "fmt", "-p", "."])
    assert result.exit_code == 0, result.output

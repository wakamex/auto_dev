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


class TestE2E:
    """Test the end to end functionality of the cli."""

    def test_repo_new(self, runner, test_clean_filesystem):
        """Test the format command works with the current package."""
        assert os.getcwd() == test_clean_filesystem
        result = runner.invoke(cli, ["repo", "new", "-t", "python"])
        assert result.exit_code == 0, result.output

    def test_repo_new_fail(self, runner, test_filesystem):
        """Test the format command works with the current package."""
        assert os.getcwd() == test_filesystem
        result = runner.invoke(cli, ["repo", "new", "-t", "python"])
        assert result.exit_code == 1, result.output

    def test_repo_new_test(self, runner, test_clean_filesystem):
        """Test the format command works with the current package."""
        assert os.getcwd() == test_clean_filesystem
        result = runner.invoke(cli, ["repo", "new", "-t", "python"])
        assert result.exit_code == 0, result.output
        result = runner.invoke(cli, ["test", "-p", "."])
        assert result.exit_code == 0, result.output

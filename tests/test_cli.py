"""Tests for the click cli."""

from pathlib import Path


def test_lint_fails(cli_runner, test_filesystem):
    """Test the lint command fails with no packages."""
    assert str(Path.cwd()) == test_filesystem
    cmd = ["adev", "-n", "0", "lint", "-p", "packages/fake"]
    runner = cli_runner(cmd)
    runner.execute()
    assert runner.return_code == 2, runner.output


def test_lints_self(cli_runner, test_filesystem):
    """Test the lint command works with the current package."""
    assert str(Path.cwd()) == test_filesystem
    cmd = ["adev", "-v", "-n", "0", "lint", "-p", "."]
    runner = cli_runner(cmd)
    result = runner.execute()
    assert result, runner.output
    assert runner.return_code == 0, runner.output


def test_formats_self(cli_runner, test_filesystem):
    """Test the format command works with the current package."""
    assert str(Path.cwd()) == test_filesystem
    cmd = ["adev", "-n", "0", "-v", "fmt", "-p", "."]
    runner = cli_runner(cmd)
    result = runner.execute()
    assert result, runner.output
    assert runner.return_code == 0, runner.output

"""
Tests for the click cli.
"""

import subprocess
from pathlib import Path
from typing import Tuple

import pytest

from auto_dev.cli import cli
from auto_dev.utils import change_dir


class BaseTestRepo:
    """Test scaffolding new repository."""

    repo_name = "dummy"
    type_of_repo: str
    make_commands: Tuple[str]

    @property
    def cli_args(self):
        """CLI arguments"""
        return ("repo", self.repo_name, "-t", self.type_of_repo)

    @property
    def repo_path(self):
        """Path of newly scaffolded repo."""
        return Path.cwd() / self.repo_name

    def test_repo_new(self, cli_runner, test_clean_filesystem):
        """Test the format command works with the current package."""

        assert test_clean_filesystem
        result = cli_runner.invoke(cli, self.cli_args)
        assert result.exit_code == 0, result.output
        assert (self.repo_path / ".git").exists()

    def test_repo_new_fail(self, cli_runner, test_filesystem):
        """Test the format command works with the current package."""

        assert test_filesystem

        self.repo_path.mkdir()
        result = cli_runner.invoke(cli, self.cli_args)
        assert result.exit_code == 1, result.output

    def test_makefile(self, cli_runner, test_clean_filesystem):
        """Test scaffolding of Makefile"""

        assert test_clean_filesystem

        result = cli_runner.invoke(cli, self.cli_args)
        makefile = self.repo_path / "Makefile"
        assert result.exit_code == 0, result.output
        assert makefile.read_text(encoding="utf-8")

        error_messages = {}
        with change_dir(self.repo_path):
            for command in self.make_commands:
                result = subprocess.run(
                    f"make {command}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                if not result.returncode == 0:
                    error_messages[command] = result.stderr
        assert not error_messages


@pytest.mark.skip(reason="Not implemented yet")
class TestRepoPython(BaseTestRepo):
    """Test scaffolding new python repository."""

    type_of_repo = "python"
    make_commands = "fmt", "lint", "test"


class TestRepoAutonomy(BaseTestRepo):
    """Test scaffolding new autonomy repository."""

    type_of_repo = "autonomy"
    make_commands = "fmt", "test", "lint", "hashes"

    def test_run_single_agent(self, cli_runner, test_clean_filesystem):
        """Test the scripts/run_single_agent.sh is generated"""

        assert test_clean_filesystem

        result = cli_runner.invoke(cli, self.cli_args)
        assert result.exit_code == 0, result.output
        expected_path = self.repo_path / "scripts" / "run_single_agent.sh"
        assert expected_path.exists()

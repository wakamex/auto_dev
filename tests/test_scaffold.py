"""
Tests for component scaffolding.
"""

import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from auto_dev.cli import cli


class TestScaffoldConnection:
    """Test scaffold connection."""

    def test_no_name_provided(self, runner, dummy_agent_tim):
        """Test no name provided."""
        result = runner.invoke(cli, ["scaffold", "connection"])
        assert result.exit_code == 2, result.output
        assert "Missing argument 'NAME'" in result.output

    # def test_scaffold_without_spec(self, runner, dummy_agent_tim):
    #     result = runner.invoke(cli, ["scaffold", "connection", "my_connection"])
    #     assert result.exit_code == 0, result.output

    def test_scaffold_with_spec_yaml(self, runner, dummy_agent_tim, caplog):
        path = Path.cwd() / ".." / "tests" / "data" / "dummy_protocol.yaml"
        result = runner.invoke(cli, ["scaffold", "connection", "my_connection", "--protocol", str(path)])
        assert result.exit_code == 0, result.output
        assert f"Read protocol specification: {path}" in caplog.text

    def test_scaffold_with_spec_readme(self, runner, dummy_agent_tim, caplog):
        path = Path.cwd() / ".." / "tests" / "data" / "dummy_protocol.md"
        result = runner.invoke(cli, ["scaffold", "connection", "my_connection", "--protocol", str(path)])
        assert result.exit_code == 0, result.output
        assert f"Read protocol specification: {path}" in caplog.text


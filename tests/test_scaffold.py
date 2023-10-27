"""Tests for the scaffold command"""

import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner
from aea.cli import cli as aea_cli

from auto_dev.cli import cli

FSM_SPEC = Path("auto_dev/data/fsm/fsm_specification.yaml").absolute()


@pytest.mark.parametrize("spec", [None, FSM_SPEC])
def test_scaffold_fsm_with_aea_run(cli_runner, spec, dummy_agent_tim):
    """Test scaffold base FSM upto `aea run`."""

    command = ["scaffold", "fsm"]
    if spec:
        command.extend(["--spec", str(spec)])

    dummy_agent_tim.exists()
    result = cli_runner.invoke(cli, command)
    assert result.exit_code == 0, result.output

    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_round_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "registration_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "reset_pause_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "termination_abci").exists()

    result = cli_runner.invoke(aea_cli, ["run"])
    assert result.exit_code == 1
    assert "An error occurred during instantiation of connection valory" in result.output
"""
Tests for component scaffolding.
"""


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


"""Tests for the scaffold command"""


from pathlib import Path

import pytest
from aea.cli import cli as aea_cli

from auto_dev.cli import cli
from auto_dev.constants import BASE_FSM_SKILLS

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

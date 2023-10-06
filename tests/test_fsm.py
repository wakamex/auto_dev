"""
This module contains tests for the fsm module.
"""

from pathlib import Path
from textwrap import dedent
import pytest

from aea.cli import cli as aea_cli
from auto_dev.cli import cli
from auto_dev.constants import DEFAULT_ENCODING, PACKAGE_DIR
from auto_dev.fsm.fsm import FsmSpec

EXAMPLE = """
alphabet_in:
- DONE
- NO_MAJORITY
- RESET_TIMEOUT
- ROUND_TIMEOUT
default_start_state: RegistrationRound
final_states: []
label: HelloWorldAbciApp
start_states:
- RegistrationRound
states:
- RegistrationRound
- CollectRandomnessRound
- PrintMessageRound
- ResetAndPauseRound
- SelectKeeperRound
transition_func:
  (CollectRandomnessRound, DONE): SelectKeeperRound
  (CollectRandomnessRound, NO_MAJORITY): CollectRandomnessRound
  (CollectRandomnessRound, ROUND_TIMEOUT): CollectRandomnessRound
  (PrintMessageRound, DONE): ResetAndPauseRound
  (PrintMessageRound, ROUND_TIMEOUT): RegistrationRound
  (RegistrationRound, DONE): CollectRandomnessRound
  (ResetAndPauseRound, DONE): CollectRandomnessRound
  (ResetAndPauseRound, NO_MAJORITY): RegistrationRound
  (ResetAndPauseRound, RESET_TIMEOUT): RegistrationRound
  (SelectKeeperRound, DONE): PrintMessageRound
  (SelectKeeperRound, NO_MAJORITY): RegistrationRound
  (SelectKeeperRound, ROUND_TIMEOUT): RegistrationRound
"""

SAMPLE_MERMAID_2 = """
stateDiagram-v2
   [*] --> CheckExpiredPositions: Start
   CheckExpiredPositions --> CloseExpiredPosition: NewExpiredPositionFound
   CheckExpiredPositions --> CheckPositions: Done

   CloseExpiredPosition --> CheckExpiredPositions: Done
   CloseExpiredPosition --> FailedTransaction: FailedToCloseExpiredPosition

   CheckPositions --> CheckBalances: Done
   CheckPositions --> CheckExpiredPositions: Failed
   CheckBalances --> CheckExpiredPositions: Failed
   CheckBalances --> CheckTickers: Done

   CheckTickers --> ExecuteArbitrumSide: ArbitrageExists
   CheckTickers --> CheckPositions: NoAction

   ExecuteArbitrumSide --> ExecuteDeribitSide: Done
   ExecuteArbitrumSide --> FailedTransaction: FailedToTransactOnArbitrum

   ExecuteDeribitSide --> Profit: SuccessfullyCapturedArbitrage
   ExecuteDeribitSide --> FailedTransaction: FailedToTransactOnDeribit

   Profit --> CheckExpiredPositions: Done
   FailedTransaction --> StopStategy: SendAlert
"""


def test_from_fsm_spec():
    """Test that we can create a FsmSpec from a yaml string."""
    fsm_spec = FsmSpec.from_yaml(EXAMPLE)
    assert fsm_spec.default_start_state == "RegistrationRound"
    assert fsm_spec.states == [
        "RegistrationRound",
        "CollectRandomnessRound",
        "PrintMessageRound",
        "ResetAndPauseRound",
        "SelectKeeperRound",
    ]


def test_to_mermaid():
    """Test that we cam convert a FsmSpec to a mermaid string."""
    fsm_spec = FsmSpec.from_yaml(EXAMPLE)
    mermaid = fsm_spec.to_mermaid()
    expected = dedent(
        """
    graph TD
      RegistrationRound
      RegistrationRound
      CollectRandomnessRound
      PrintMessageRound
      ResetAndPauseRound
      SelectKeeperRound
      CollectRandomnessRound -->|DONE| SelectKeeperRound
      CollectRandomnessRound -->|NO_MAJORITY| CollectRandomnessRound
      CollectRandomnessRound -->|ROUND_TIMEOUT| CollectRandomnessRound
      PrintMessageRound -->|DONE| ResetAndPauseRound
      PrintMessageRound -->|ROUND_TIMEOUT| RegistrationRound
      RegistrationRound -->|DONE| CollectRandomnessRound
      ResetAndPauseRound -->|DONE| CollectRandomnessRound
      ResetAndPauseRound -->|NO_MAJORITY| RegistrationRound
      ResetAndPauseRound -->|RESET_TIMEOUT| RegistrationRound
      SelectKeeperRound -->|DONE| PrintMessageRound
      SelectKeeperRound -->|NO_MAJORITY| RegistrationRound
      SelectKeeperRound -->|ROUND_TIMEOUT| RegistrationRound
    """
    )
    assert mermaid == expected


def test_from_mermaid():
    """Test that we can create a FsmSpec from a mermaid string."""
    fsm_spec = FsmSpec.from_yaml(EXAMPLE)
    mermaid = fsm_spec.to_mermaid()
    fsm_spec_from_mermaid = FsmSpec.from_mermaid(mermaid)

    # we check the atrtibutes
    assert fsm_spec_from_mermaid.default_start_state == fsm_spec.default_start_state
    assert set(fsm_spec_from_mermaid.states) == set(fsm_spec.states)
    assert set(fsm_spec_from_mermaid.alphabet_in) == set(fsm_spec.alphabet_in)
    assert fsm_spec_from_mermaid.transition_func == fsm_spec.transition_func


def test_to_string():
    """We test whether to output of to_string will match EXAMPLE"""
    fsm_spec = FsmSpec.from_yaml(EXAMPLE)
    new_fsm = fsm_spec.to_string()
    new_fsm_spec = FsmSpec.from_yaml(new_fsm)
    assert fsm_spec.default_start_state == new_fsm_spec.default_start_state
    assert fsm_spec.states == new_fsm_spec.states
    assert fsm_spec.alphabet_in == new_fsm_spec.alphabet_in
    assert fsm_spec.transition_func == new_fsm_spec.transition_func


def test_from_mermaid_fsm():
    """Test that we can create a FsmSpec from a mermaid string."""
    fsm_spec = FsmSpec.from_mermaid(SAMPLE_MERMAID_2)
    mermaid = fsm_spec.to_mermaid()
    fsm_spec_from_mermaid = FsmSpec.from_mermaid(mermaid)

    # we check the atrtibutes
    assert fsm_spec_from_mermaid.default_start_state == fsm_spec.default_start_state
    assert set(fsm_spec_from_mermaid.states) == set(fsm_spec.states)
    assert set(fsm_spec_from_mermaid.alphabet_in) == set(fsm_spec.alphabet_in)
    assert fsm_spec_from_mermaid.transition_func == fsm_spec.transition_func


def test_base_fsm(runner, dummy_agent_tim):
    """Test scaffold base FSM."""

    dummy_agent_tim.exists()
    result = runner.invoke(cli, ["fsm", "base"])
    assert result.exit_code == 0, result.output

    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_round_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "registration_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "reset_pause_abci").exists()


def test_base_fsm_with_spec(runner, dummy_agent_tim):
    """Test scaffold base FSM."""

    dummy_agent_tim.exists()

    name = "dummy"
    path = Path(PACKAGE_DIR) / "data" / "fsm" / "fsm_specification.yaml"
    result = runner.invoke(cli, ["fsm", "base", name, str(path)])
    assert result.exit_code == 0, result.output

    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_round_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "registration_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "reset_pause_abci").exists()

    new_skill_path = Path.cwd() / "skills" / name / "fsm_specification.yaml"
    assert new_skill_path.exists()
    assert new_skill_path.read_text(encoding=DEFAULT_ENCODING) == path.read_text(encoding=DEFAULT_ENCODING)


def test_base_fsm_aea_run_missing_overwrites(runner, dummy_agent_tim):
    """Test scaffold base FSM upto `aea run`."""

    dummy_agent_tim.exists()
    result = runner.invoke(cli, ["fsm", "base"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(aea_cli, ["run",])
    assert result.exit_code == 1
    assert "An error occurred during instantiation of connection valory" in result.output

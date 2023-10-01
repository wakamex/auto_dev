"""
Implement fsm tooling
"""

from pathlib import Path

import rich_click as click
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE

from auto_dev.base import build_cli
from auto_dev.cli_executor import CommandExecutor
from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.fsm.fsm import FsmSpec
from auto_dev.utils import get_logger

logger = get_logger()

cli = build_cli(plugins=False)

# we have a fsm command group

SKILLS = {
    "registration_abci": "bafybeig3jo3fhcxz7xgwpxnmf74ann2bwlqyaq2466wrkg5mbc33wmpk6y",
    "reset_pause_abci": "bafybeicuma62mkfb36ygsycufhjqt6jqffi7zhhuxdlgdvmq6kcjl2ebm4",
}


@cli.group()
def fsm():
    """
    Implement fsm tooling
    """


@fsm.command()
@click.argument("name", type=str, default=None, required=False)
@click.argument("path", type=click.Path(exists=True, file_okay=True), default=None, required=False)
def base(name, path):
    """
    Scaffold a base FSM.

    usage: `adev fsm base [name] [fsm_specification.yaml]`
    """
    if not Path(DEFAULT_AEA_CONFIG_FILE).exists():
        raise ValueError(f"No {DEFAULT_AEA_CONFIG_FILE} found in current directory")

    if not bool(name) == bool(path):
        raise ValueError("Either both or neither the name and fsm spec need to be provided")

    skills = "registration_abci", "reset_pause_abci"
    for skill in skills:
        command = CommandExecutor(["autonomy", "add", "skill", SKILLS[skill]])
        result = command.execute(verbose=True)
        if not result:
            raise ValueError(f"Adding failed for skill: {skill}")
    if not name and not path:
        return

    command = CommandExecutor(["autonomy", "scaffold", "fsm", name, "--spec", str(path)])
    result = command.execute(verbose=True)
    if not result:
        raise ValueError(f"FSM scaffolding failed for spec: {path}")


@fsm.command()
@click.argument("fsm-spec", type=click.File("r", encoding=DEFAULT_ENCODING))
@click.option("--in-type", type=click.Choice(["mermaid", "fsm-spec"], case_sensitive=False))
@click.option("--output", type=click.Choice(["mermaid", "fsm-spec"], case_sensitive=False))
def from_file(fsm_spec: str, in_type: str, output: str):
    """We template from a file."""
    # we need perform the following steps:
    # 1. load the yaml file
    # 2. validate the yaml file using the open-autonomy fsm tooling
    # 3. perform the generation command
    # 4. write the generated files to disk
    # 5. perform the cleanup commands
    # 5a. clean the tests
    # 5b. clean the payloads
    # 6. perform updates of the generated files

    if in_type == "mermaid":
        _fsm_spec = fsm_spec.read()
        fsm = FsmSpec.from_mermaid(_fsm_spec)
    else:
        fsm = FsmSpec.from_yaml(fsm_spec)

    if output == "mermaid":
        print(fsm.to_mermaid())
    else:
        print(fsm.to_string())

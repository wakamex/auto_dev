"""Implement fsm tooling."""

import rich_click as click

from auto_dev.base import build_cli
from auto_dev.utils import get_logger, snake_to_camel
from auto_dev.fsm.fsm import FsmSpec
from auto_dev.constants import DEFAULT_ENCODING


logger = get_logger()

cli = build_cli(plugins=False)


# we have a fsm command group
@cli.group()
def fsm() -> None:
    """Implement fsm tooling."""


@fsm.command()
@click.argument("fsm-spec", type=click.File("r", encoding=DEFAULT_ENCODING))
@click.argument("fsm_name", type=str)
@click.option("--in-type", type=click.Choice(["mermaid", "fsm-spec"], case_sensitive=False))
@click.option("--output", type=click.Choice(["mermaid", "fsm-spec"], case_sensitive=False))
def from_file(fsm_spec: str, fsm_name: str, in_type: str, output: str) -> None:
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

    def validate_name(name: str) -> str:
        if not name:
            raise ValueError("Name must not be empty.")
        if not name.endswith("AbciApp"):
            raise ValueError("Name must end with AbciApp.")
        return name

    fsm.label = validate_name(fsm_name)

    if output == "mermaid":
        output = fsm.to_mermaid()
    else:   
        output = fsm.to_string()

    click.echo(output)


"""
Implement fsm tooling
"""

import rich_click as click

from auto_dev.base import build_cli
from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.fsm.fsm import FsmSpec
from auto_dev.utils import get_logger

logger = get_logger()

cli = build_cli(plugins=False)

# we have a fsm command group


@cli.group()
def fsm():
    """
    Implement fsm tooling
    """


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

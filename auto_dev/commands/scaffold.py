"""Module to allow the scaffolding of contracts.
Contains a BlockExplorer class to allow the user to interact with
the blockchain explorer.

Also contains a Contract, which we will use to allow the user to;
- generate the open-aea contract class.
- generate the open-aea contract tests.

"""

import json
from typing import Optional
from pathlib import Path

import yaml
import tomli
import rich_click as click
from web3 import Web3
from jinja2 import Environment, FileSystemLoader
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE, PROTOCOL_LANGUAGE_PYTHON, SUPPORTED_PROTOCOL_LANGUAGES
from aea.configurations.data_types import PublicId
from aea.configurations.base import PublicId

from auto_dev.base import build_cli
from auto_dev.enums import FileType, BehaviourTypes
from auto_dev.utils import load_aea_ctx, remove_suffix, camel_to_snake, read_from_file
from auto_dev.constants import BASE_FSM_SKILLS, DEFAULT_ENCODING, JINJA_TEMPLATE_FOLDER
from auto_dev.cli_executor import CommandExecutor
from auto_dev.handlers.base import HandlerTypes, HandlerScaffolder
from auto_dev.dao.scaffolder import DAOScaffolder
from auto_dev.contracts.contract import DEFAULT_NULL_ADDRESS
from auto_dev.handler.scaffolder import HandlerScaffoldBuilder
from auto_dev.dialogues.scaffolder import DialogueTypes, DialogueScaffolder
from auto_dev.protocols.scaffolder import ProtocolScaffolder
from auto_dev.behaviours.scaffolder import BehaviourScaffolder
from auto_dev.connections.scaffolder import ConnectionScaffolder
from auto_dev.contracts.block_explorer import BlockExplorer
from auto_dev.contracts.contract_scafolder import ContractScaffolder


cli = build_cli()


# we have a new command group called scaffold.
@cli.group()
def scaffold() -> None:
    """Scaffold a (set of) components."""


def validate_address(address: str, logger, contract_name: str = None) -> Optional[str]:
    """Convert address to checksum format and validate it."""
    if address == DEFAULT_NULL_ADDRESS:
        return address
    try:
        return Web3.to_checksum_address(str(address))
    except ValueError as e:
        name_suffix = f" for {contract_name}" if contract_name else ""
        logger.error(f"Invalid address format{name_suffix}: {e}")
        return None


def validate_abi_version(abi_data):
    """Validate that ABI is Solidity 0.6+ format."""
    if not isinstance(abi_data, list):
        raise TypeError("Invalid ABI format: Expected a list of function/event definitions")

    function_entries = [item for item in abi_data if item.get("type") == "function"]
    if not function_entries:
        raise TypeError("Invalid ABI: No function definitions found")

    for function in function_entries:
        if "constant" in function:
            raise TypeError(
                "Outdated ABI format detected (pre-0.6 Solidity). " "Please provide an ABI from Solidity 0.6 or later"
            )

        if "stateMutability" not in function:
            raise TypeError(
                "Outdated ABI format detected (pre-0.6 Solidity). " "Please provide an ABI from Solidity 0.6 or later"
            )

        for param in function.get("inputs", []) + function.get("outputs", []):
            if "internalType" not in param:
                raise TypeError(
                    "Outdated ABI format detected (pre-0.6 Solidity). "
                    "Please provide an ABI from Solidity 0.6 or later"
                )


def _process_from_file(ctx, yaml_dict, network, read_functions, write_functions, logger):
    """Process contracts from a file."""
    for contract_name, contract_address in yaml_dict["contracts"].items():
        validated_address = validate_address(contract_address, logger, contract_name)
        if validated_address is None:
            continue
        ctx.invoke(
            contract,
            address=validated_address,
            name=camel_to_snake(contract_name),
            network=yaml_dict.get("network", network),
            read_functions=read_functions,
            write_functions=write_functions,
        )


def _get_author_from_aea_config(logger):
    """Extract author from aea-config.yaml."""
    config_path = Path.cwd() / DEFAULT_AEA_CONFIG_FILE
    if config_path.exists():
        try:
            with open(config_path, encoding=DEFAULT_ENCODING) as f:
                first_doc = f.read().split('---')[0]
                config_data = yaml.safe_load(first_doc)
            author = config_data.get("author")
            if author:
                return author
        except (yaml.YAMLError, KeyError) as e:
            logger.warning(f"Failed to parse {DEFAULT_AEA_CONFIG_FILE}: {e}")
    return None


@scaffold.command()
@click.argument("name", default=None, required=False)
@click.option("--address", default=DEFAULT_NULL_ADDRESS, required=False, help="The address of the contract.")
@click.option("--author", required=False, help="The author of the contract.")
@click.option("--from-file", default=None, help="Ingest a file containing a list of addresses and names.")
@click.option("--from-abi", default=None, help="Ingest an ABI file to scaffold a contract.")
@click.option("--network", default="ethereum", help="The network to fetch the ABI from (e.g., ethereum, polygon)")
@click.option("--read-functions", default=None, help="Comma separated list of read functions to scaffold.")
@click.option("--write-functions", default=None, help="Comma separated list of write functions to scaffold.")
@click.pass_context
def contract(ctx, address, name, author, network, read_functions, write_functions, from_abi, from_file):
    """Scaffold a contract."""
    logger = ctx.obj["LOGGER"]

    if from_file is None and not name:
        logger.error("Must provide a name when not using --from-file")
        return

    if author is None:
        aea_author = _get_author_from_aea_config(logger)
        if aea_author:
            try:
                author = PublicId.from_str(f"{aea_author}/default")
            except ValueError:
                logger.error("Invalid author format in aea-config.yaml")
                return
        else:
            logger.error("Author is required. Please provide --author parameter or ensure it's specified in aea-config.yaml")
            return

    if name:
        name = name.replace(" ", "_").replace("/", "_")

    if from_file is not None:
        with open(from_file, encoding=DEFAULT_ENCODING) as file_pointer:
            yaml_dict = yaml.safe_load(file_pointer)
        _process_from_file(ctx, yaml_dict, network, read_functions, write_functions, logger)
        return

    validated_address = validate_address(address, logger)
    if validated_address is None:
        return

    if from_abi is not None:
        logger.info(f"Using ABI file: {from_abi}")
        try:
            with open(from_abi, "r") as f:
                abi_data = json.loads(f.read())
            validate_abi_version(abi_data)
            scaffolder = ContractScaffolder(block_explorer=None, author=author.author)
            new_contract = scaffolder.from_abi(from_abi, validated_address, name)
            logger.info(f"New contract scaffolded at {new_contract.path}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error processing ABI file: {str(e)}")
            return

    else:
        logger.info(f"Fetching ABI for contract at address: {validated_address} on network: {network}")
        block_explorer = BlockExplorer(f"https://abidata.net", network=network)
        scaffolder = ContractScaffolder(block_explorer=block_explorer, author=author.author)
        logger.info("Getting ABI from abidata.net")
        new_contract = scaffolder.from_block_explorer(validated_address, name)

    logger.info("Generating openaea contract with aea scaffolder.")
    contract_path = scaffolder.generate_openaea_contract(new_contract)
    logger.info("Writing abi to file, Updating contract.yaml with build path. Parsing functions.")
    new_contract.process()
    logger.info("Read Functions extracted:")
    for function in new_contract.read_functions:
        logger.info(f"    {function.name}")
    logger.info("Write Functions extracted:")
    for function in new_contract.write_functions:
        logger.info(f"    {function.name}")

    logger.info("Events extracted:")
    for event in new_contract.events:
        logger.info(f"    {event.name}")

    logger.info(f"New contract scaffolded at {contract_path}")


@scaffold.command()
@click.option("--spec", default=None, required=False)
def fsm(spec) -> None:
    """Scaffold a FSM.

    usage: `adev scaffold fsm [--spec fsm_specification.yaml]`
    """
    if not Path(DEFAULT_AEA_CONFIG_FILE).exists():
        msg = f"No {DEFAULT_AEA_CONFIG_FILE} found in current directory"
        raise ValueError(msg)

    for skill, ipfs_hash in BASE_FSM_SKILLS.items():
        command = CommandExecutor(["autonomy", "add", "skill", ipfs_hash])
        result = command.execute(verbose=True)
        if not result:
            msg = f"Adding failed for skill: {skill}"
            raise ValueError(msg)

    if not spec:
        return

    path = Path(spec)
    if not path.exists():
        msg = f"Specified spec '{path}' does not exist."
        raise click.ClickException(msg)

    fsm_spec = yaml.safe_load(path.read_text(encoding=DEFAULT_ENCODING))
    name = camel_to_snake(remove_suffix(fsm_spec["label"], "App"))

    command = CommandExecutor(["autonomy", "scaffold", "fsm", name, "--spec", str(spec)])
    result = command.execute(verbose=True)
    if not result:
        msg = f"FSM scaffolding failed for spec: {spec}"
        raise ValueError(msg)


@scaffold.command()
@click.argument("protocol_specification_path", type=str, required=True)
@click.option(
    "--l",
    "language",
    type=click.Choice(SUPPORTED_PROTOCOL_LANGUAGES),
    required=False,
    default=PROTOCOL_LANGUAGE_PYTHON,
    help="Specify the language in which to generate the protocol package.",
)
@click.pass_context
def protocol(ctx, protocol_specification_path: str, language: str) -> None:
    """Scaffold a protocol."""
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]
    scaffolder = ProtocolScaffolder(protocol_specification_path, language, logger=logger, verbose=verbose)
    scaffolder.generate()


@scaffold.command()
@click.argument("name", default=None, required=True)
@click.option("--protocol", type=PublicId.from_str, required=True, help="the PublicId of a protocol.")
@click.pass_context
@load_aea_ctx
def connection(  # pylint: disable=R0914
    ctx,
    name,
    protocol: PublicId,
) -> None:
    """Scaffold a connection."""
    logger = ctx.obj["LOGGER"]

    if protocol not in ctx.aea_ctx.agent_config.protocols:
        msg = f"Protocol {protocol} not found in agent configuration."
        raise click.ClickException(msg)

    scaffolder = ConnectionScaffolder(ctx, name, protocol)
    scaffolder.generate()

    connection_path = Path.cwd() / "connections" / name
    logger.info(f"New connection scaffolded at {connection_path}")


@scaffold.command()
@click.argument("spec_file", type=click.Path(exists=True), required=True)
@click.argument("public_id", type=PublicId.from_str, required=True)
@click.option("--new-skill", is_flag=True, default=False, help="Create a new skill")
@click.option("--auto-confirm", is_flag=True, default=False, help="Auto confirm all actions")
@click.pass_context
def handler(ctx, spec_file, public_id, new_skill, auto_confirm) -> int:
    """Generate an AEA handler from an OpenAPI 3 specification."""
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]

    if not Path(DEFAULT_AEA_CONFIG_FILE).exists():
        msg = f"No {DEFAULT_AEA_CONFIG_FILE} found in current directory"
        raise ValueError(msg)

    scaffolder = (
        HandlerScaffoldBuilder()
        .create_scaffolder(spec_file, public_id, logger, verbose, new_skill=new_skill, auto_confirm=auto_confirm)
        .build()
    )

    scaffolder.scaffold()

    return 0


@scaffold.command()
@click.argument("spec_file", type=click.Path(exists=True), required=True)
@click.option("-tsa", "--target-speech-acts", default=None, help="Comma separated list of speech acts to scaffold.")
@click.option("--auto-confirm", is_flag=True, default=False, help="Auto confirm all actions")
@click.option(
    "--behaviour-type",
    type=click.Choice([f.value for f in (BehaviourTypes.metrics, BehaviourTypes.simple_fsm)]),
    required=True,
    help="The type of behaviour to generate.",
    default=BehaviourTypes.metrics,
)
@click.pass_context
def behaviour(
    ctx,
    spec_file,
    behaviour_type,
    auto_confirm,
    target_speech_acts,
) -> None:
    """
    Generate an AEA handler from an OpenAPI 3 specification.

    Example:
    ```
    adev scaffold behaviour openapi.yaml --behaviour-type metrics
    ```

    """
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]

    scaffolder = BehaviourScaffolder(
        spec_file,
        behaviour_type=BehaviourTypes[behaviour_type],
        logger=logger,
        verbose=verbose,
        auto_confirm=auto_confirm,
    )
    scaffolder.scaffold(
        target_speech_acts=target_speech_acts,
    )


@scaffold.command()
@click.argument("spec_file", type=click.Path(exists=True), required=True)
@click.option("-tsa", "--target-speech-acts", default=None, help="Comma separated list of speech acts to scaffold.")
@click.option("--auto-confirm", is_flag=True, default=False, help="Auto confirm all actions")
@click.option(
    "--handler_type",
    type=click.Choice([HandlerTypes.simple]),
    required=True,
    help="The type of behaviour to generate.",
    default=HandlerTypes.simple,
)
@click.pass_context
def handlers(ctx, spec_file, handler_type, auto_confirm, target_speech_acts) -> None:
    """
    Generate an AEA handler from an OpenAPI 3 specification.

    Example:
    ```
    adev scaffold behaviour openapi.yaml --behaviour-type metrics
    ```

    """
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]

    scaffolder = HandlerScaffolder(
        spec_file, handler_type=handler_type, logger=logger, verbose=verbose, auto_confirm=auto_confirm
    )
    scaffolder.scaffold(
        target_speech_acts=target_speech_acts,
    )


@scaffold.command()
@click.argument("spec_file", type=click.Path(exists=True), required=True)
@click.option("-tsa", "--target-speech-acts", default=None, help="Comma separated list of speech acts to scaffold.")
@click.option("--auto-confirm", is_flag=True, default=False, help="Auto confirm all actions")
@click.option(
    "--dialogue-type",
    type=click.Choice([DialogueTypes.simple]),
    required=True,
    help="The type of behaviour to generate.",
    default=DialogueTypes.simple,
)
@click.pass_context
def dialogues(ctx, spec_file, dialogue_type, auto_confirm, target_speech_acts) -> None:
    """
    Generate an AEA handler from an OpenAPI 3 specification.

    Example:
    ```
    adev scaffold behaviour openapi.yaml --behaviour-type metrics
    ```

    """
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]

    scaffolder = DialogueScaffolder(
        spec_file, dialogue_type=dialogue_type, logger=logger, verbose=verbose, auto_confirm=auto_confirm
    )
    scaffolder.scaffold(
        target_speech_acts=target_speech_acts,
    )


@scaffold.command()
@click.pass_context
def tests(
    ctx,
) -> None:
    """Generate tests for an aea component in the current directory
    AEA handler from an OpenAPI 3 specification.
    """
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]
    env = Environment(loader=FileSystemLoader(Path(JINJA_TEMPLATE_FOLDER, "tests", "customs")), autoescape=True)
    template = env.get_template("test_custom.jinja")
    output = template.render(
        name="test",
    )
    if verbose:
        logger.info(f"Generated tests: {output}")


@scaffold.command()
@click.option("--auto-confirm", is_flag=True, default=False, help="Auto confirm all actions")
@click.pass_context
def dao(ctx, auto_confirm) -> None:
    """Scaffold Data Access Objects (DAOs) and generate test script based on an OpenAPI 3 specification."""
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]

    if not Path("component.yaml").exists():
        msg = "component.yaml not found in the current directory."
        raise ValueError(msg)

    customs_config = read_from_file(Path("component.yaml"), FileType.YAML)
    if customs_config is None:
        msg = "Error: customs_config is None. Unable to process."
        raise ValueError(msg)

    api_spec_path = customs_config.get("api_spec")
    if not api_spec_path:
        msg = "Error: api_spec key not found in component.yaml"
        raise ValueError(msg)

    component_author = customs_config.get("author")
    component_name = customs_config.get("name")
    public_id = PublicId(component_author, component_name.split(":")[0])

    try:
        scaffolder = DAOScaffolder(logger, verbose, auto_confirm, public_id)
        scaffolder.scaffold()
    except Exception as e:
        logger.exception(f"Error during DAO scaffolding and test generation: {e}")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

"""
Module to allow the scaffolding of contracts.
Contains a BlockExplorer class to allow the user to interact with
the blockchain explorer.

Also contains a Contract, which we will use to allow the user to;
- generate the open-aea contract class.
- generate the open-aea contract tests.

"""

import rich_click as click
import yaml

from auto_dev.base import build_cli
from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.contracts.block_explorer import BlockExplorer
from auto_dev.contracts.contract_scafolder import ContractScaffolder
from auto_dev.contracts.utils import from_camel_case_to_snake_case

cli = build_cli()


# we have a new command group called scaffold.
@cli.group()
def scaffold():
    """
    Scaffold a contract.
    """


@scaffold.command()
@click.argument("address", default=None, required=False)
@click.argument("name", default=None, required=False)
@click.option("--from-file", default=None, help="Ingest a file containing a list of addresses and names.")
@click.option("--block-explorer-url", default="https://api.etherscan.io/api")
@click.option("--block-explorer-api-key", required=True)
@click.option("--read-functions", default=None, help="Comma separated list of read functions to scaffold.")
@click.option("--write-functions", default=None, help="Comma separated list of write functions to scaffold.")
@click.pass_context
def contract(  # pylint: disable=R0914
    ctx, address, name, block_explorer_url, block_explorer_api_key, read_functions, write_functions, from_file
):
    """
    Scaffold a contract.
    """
    logger = ctx.obj["LOGGER"]
    if address is None and name is None and from_file is None:
        logger.error("Must provide either an address and name or a file containing a list of addresses and names.")
        return
    if from_file is not None:
        with open(from_file, "r", encoding=DEFAULT_ENCODING) as file_pointer:
            yaml_dict = yaml.safe_load(file_pointer)
        for contract_name, contract_address in yaml_dict["contracts"].items():
            ctx.invoke(
                contract,
                address=str(contract_address),
                name=from_camel_case_to_snake_case(contract_name),
                block_explorer_url=yaml_dict["block_explorer_url"],
                block_explorer_api_key=block_explorer_api_key,
                read_functions=read_functions,
                write_functions=write_functions,
            )

        return
    logger.info(f"Using block explorer url: {block_explorer_url}")
    logger.info(f"Scaffolding contract at address: {address} with name: {name}")

    block_explorer = BlockExplorer(block_explorer_url, block_explorer_api_key)
    scaffolder = ContractScaffolder(block_explorer=block_explorer)
    logger.info("Getting abi from block explorer.")
    new_contract = scaffolder.from_block_explorer(address, name)
    logger.info("Generating openaea contract with aea scaffolder.")
    contract_path = scaffolder.generate_openaea_contract(new_contract)
    logger.info("Writing abi to file, Updating contract.yaml with build path. Parsing functions.")
    new_contract.process()
    logger.info(f"Read Functions: {new_contract.read_functions}")
    logger.info(f"Write Functions: {new_contract.write_functions}")
    logger.info(f"New contract scaffolded at {contract_path}")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

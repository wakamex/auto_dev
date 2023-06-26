"""
Module to allow the scaffolding of contracts.
Contains a BlockExplorer class to allow the user to interact with
the blockchain explorer.

Also contains a Contract, which we will use to allow the user to;
- generate the open-aea contract class.
- generate the open-aea contract tests.

"""
import json
import os
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import requests
import rich_click as click
import yaml
from web3 import Web3

from auto_dev.base import build_cli
from auto_dev.cli_executor import CommandExecutor
from auto_dev.constants import DEFAULT_ENCODING, DEFAULT_TIMEOUT

cli = build_cli()

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))


@dataclass
class BlockExplorer:
    """
    Class to interact with the blockchain explorer.
    """

    url: str
    api_key: str = None

    def _authenticated_request(self, url: str, params: dict = None):
        """
        Make an authenticated request.
        The api key is encoded into the url.
        """
        if not params:
            params = {}
        params["apiKey"] = self.api_key
        return requests.get(
            url,
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )

    def get_abi(self, address: str):
        """
        Get the abi for the contract at the address.
        """
        url = self.url + "/api?module=contract&action=getabi&address=" + address
        response = self._authenticated_request(url)
        if response.status_code != 200:
            raise ValueError(f"Failed to get abi for address {address} with status code {response.status_code}")
        return json.loads(json.loads(response.text)['result'])


def from_snake_case(string: str):
    """
    Convert a string from snake case to camel case.
    """
    return "".join(word.capitalize() for word in string.split("_"))


class Contract:
    """
    Class to scaffold a contract.
    """

    author: str
    name: str
    abi: dict
    address: str
    read_functions: List = []
    write_functions: List = []
    path: Path

    def parse_functions(self):
        """
        Get the functions from the abi.
        """
        abi_path = self.path / "build" / f"{self.name}.json"
        if not abi_path.exists():
            raise ValueError(f"Abi file {abi_path} does not exist.")
        with abi_path.open("r", encoding=DEFAULT_ENCODING) as file_pointer:
            abi = json.load(file_pointer)['abi']
        w3_contract = w3.eth.contract(address=self.address, abi=abi)
        for function in w3_contract.all_functions():
            if function.abi['stateMutability'] == 'view':
                self.read_functions.append(function)
            elif function.abi['stateMutability'] == 'nonpayable':
                self.write_functions.append(function)
            else:
                raise ValueError(f"Function {function} has unknown state mutability.")

    def __init__(self, author: str, name: str, abi: dict, address: str):
        """
        Initialise the contract.
        """
        self.author = author
        self.name = name
        self.abi = abi
        self.address = address
        self.path = Path.cwd() / "packages" / self.author / "contracts" / self.name

    def write_abi_to_file(self):
        """
        Write the abi to a file.
        """
        build_path = self.path / "build" / f"{self.name}.json"
        if build_path.exists():
            raise ValueError(f"Build file {build_path} already exists.")
        build_path.parent.mkdir(parents=False)
        with build_path.open("w", encoding=DEFAULT_ENCODING) as file_pointer:
            output = {
                "abi": self.abi,
                "_format": "",
                "bytecode": "",
                "sourceName": "",
                "deployedBytecode": "",
                "deployedLinkReferences": "",
            }
            json.dump(output, file_pointer, indent=4)

    def update_contract_yaml(self):
        """
        Perform an update for the contract,yaml to specify the
        """
        contract_yaml_path = self.path / "contract.yaml"
        if not contract_yaml_path.exists():
            raise ValueError(f"Contract yaml file {contract_yaml_path} does not exist.")
        with contract_yaml_path.open("r", encoding=DEFAULT_ENCODING) as file_pointer:
            contract_yaml = yaml.safe_load(file_pointer)
        contract_yaml["contract_interface_paths"]["ethereum"] = f"build/{self.name}.json"
        contract_yaml["class_name"] = from_snake_case(self.name)
        with contract_yaml_path.open("w", encoding=DEFAULT_ENCODING) as file_pointer:
            yaml.dump(contract_yaml, file_pointer, sort_keys=False)

    def update_contract_py(self):
        """
        Update the contract.py file.
        - update the class name.
        - update the contract_id     contract_id = PublicId.from_str("open_aea/scaffold:0.1.0")

        """
        contract_py_path = self.path / "contract.py"
        with contract_py_path.open("r", encoding=DEFAULT_ENCODING) as file_pointer:
            contract_py = file_pointer.read()
        contract_py = contract_py.replace("class MyScaffoldContract", f"class {from_snake_case(self.name)}")
        contract_py = contract_py.replace(
            'contract_id = PublicId.from_str("open_aea/scaffold:0.1.0")',
            "contract_id = PUBLIC_ID",
        )
        contract_py = contract_py.replace(
            "from aea.configurations.base import PublicId",
            f"from packages.{self.author}.contracts,{self.name} import PUBLIC_ID",
        )
        with contract_py_path.open("w", encoding=DEFAULT_ENCODING) as file_pointer:
            file_pointer.write(contract_py)

    def update_contract_init__(self):
        """
        Append the Public
        """
        init_py_path = self.path / "__init__.py"
        public_id = f"PublicId.from_str('{self.author}/{self.name}:0.1.0')"
        with init_py_path.open("a", encoding=DEFAULT_ENCODING) as file_pointer:
            file_pointer.write("\nfrom aea.configurations.base import PublicId\n")
            file_pointer.write(f"\nPUBLIC_ID = {public_id}\n")

    def update_all(self):
        """
        Scaffold the contract.
        """
        self.update_contract_yaml()
        self.update_contract_py()
        self.update_contract_init__()


@contextmanager
def isolated_file_system():
    """
    Context manager to create an isolated file system.
    And to navigate to it and then to clean it up.
    """
    original_path = Path.cwd()
    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        yield Path(temp_dir)
    os.chdir(original_path)


@dataclass
class ContractScaffolder:
    """
    Class to scaffold a contract.
    """

    author: str = "eightballer"

    def from_block_explorer(self, block_explorer: BlockExplorer, address: str, name: str):
        """
        Scaffold a contract from a block explorer.
        """
        abi = block_explorer.get_abi(address)
        return Contract(abi=abi, name=name, address=address, author=self.author)

    def generate_openaea_contract(self, contract: Contract):
        """
        Generate the open-aea contract.
        We will use the contract name to generate the class name.
        We need to;
        - use the temporary directory context manager.
        - create an agent
        - cd into the agent directory
        - scaffold the contract using the name.
        - create a new directory for the contract in the original directory.
        - copy the contract to the new directory.
        """
        verbose = False

        if contract.path.exists():
            raise ValueError(f"Contract {contract.name} already exists.")
        contract.path.parent.mkdir(parents=True)

        init_cmd = f"aea init --author {self.author} --reset --ipfs --remote".split(" ")
        if not CommandExecutor(init_cmd).execute(verbose=verbose):
            raise ValueError("Failed to initialise agent lib.")

        with isolated_file_system():
            if not CommandExecutor("aea create myagent".split(" ")).execute(verbose=verbose):
                raise ValueError("Failed to create agent.")
            os.chdir("myagent")
            if not CommandExecutor(f"aea scaffold contract {contract.name}".split(" ")).execute(verbose=verbose):
                raise ValueError("Failed to scaffold contract.")
            shutil.copytree(
                f"contracts/{contract.name}",
                contract.path,
            )
        return contract.path


# we have a new command group called scaffold.
@cli.group()
def scaffold():
    """
    Scaffold a contract.
    """


@scaffold.command()
@click.argument("address")
@click.argument("name")
@click.option("--block-explorer-url", default="https://api.etherscan.io/api")
@click.option("--block-explorer-api-key", default=None)
@click.option("--read-functions", default=None, help="Comma separated list of read functions to scaffold.")
@click.option("--write-functions", default=None, help="Comma separated list of write functions to scaffold.")
@click.pass_context
def contract(ctx, address, name, block_explorer_url, block_explorer_api_key, read_functions, write_functions):
    """
    Scaffold a contract.
    """
    logger = ctx.obj["LOGGER"]
    logger.info(f"Scaffolding contract at address: {address} with name: {name}")
    logger.info(f"Using block explorer url: {block_explorer_url}")
    block_explorer = BlockExplorer(block_explorer_url, block_explorer_api_key)
    scaffolder = ContractScaffolder()

    logger.info("Getting abi from block explorer.")
    new_contract = scaffolder.from_block_explorer(block_explorer, address, name)
    logger.info("Generating openaea contract with aea scaffolder.")
    contract_path = scaffolder.generate_openaea_contract(new_contract)
    logger.info("Writing abi to file.")
    new_contract.write_abi_to_file()
    logger.info("Updating contract.yaml with build path.")
    new_contract.update_all()
    logger.info("Parsing functions.")
    new_contract.parse_functions()

    if read_functions:
        for read_function in read_functions.split(","):
            if read_function not in [f.fn_name for f in new_contract.read_functions]:
                raise ValueError(f"Read function {read_function} not in new_contract.")

    if write_functions:
        for write_function in write_functions.split(","):
            if write_function not in [f.fn_name for f in new_contract.write_functions]:
                raise ValueError(f"Write function {write_function} not in new_contract.")

    logger.info(f"Read Functions: {new_contract.read_functions}")
    logger.info(f"Write Functions: {new_contract.write_functions}")

    logger.info(f"New contract scaffolded at {contract_path}")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

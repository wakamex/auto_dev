"""
Module to represent a contract.
"""
import json
from pathlib import Path
from typing import List, Optional

import yaml
from web3 import Web3

from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.contracts.contract_functions import ReadContractFunction
from auto_dev.contracts.function import Function
from auto_dev.contracts.utils import from_snake_case_to_camel_case


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
        w3_contract = self.web3.eth.contract(address=self.address, abi=abi)
        for function in w3_contract.all_functions():
            mutability = function.abi['stateMutability']
            if mutability in ['view', "pure"]:
                queue = self.read_functions
            elif mutability in ['nonpayable', 'payable']:
                queue = self.write_functions
            else:
                raise ValueError(f"Function {function} has unknown state mutability: {mutability}")
            queue.append(Function(function.abi))

    def __init__(self, author: str, name: str, abi: dict, address: str, web3: Optional[Web3] = None):
        """
        Initialise the contract.
        """
        self.author = author
        self.name = name
        self.abi = abi
        self.address = address
        self.path = Path.cwd() / "packages" / self.author / "contracts" / self.name
        self.web3 = web3 if web3 is not None else Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

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
        contract_yaml["class_name"] = from_snake_case_to_camel_case(self.name)
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
        contract_py = contract_py.replace(
            "class MyScaffoldContract", f"class {from_snake_case_to_camel_case(self.name)}"
        )
        contract_py = contract_py.replace(
            'contract_id = PublicId.from_str("open_aea/scaffold:0.1.0")',
            "contract_id = PUBLIC_ID",
        )
        contract_py = contract_py.replace(
            "from aea.configurations.base import PublicId",
            f"from packages.{self.author}.contracts.{self.name} import PUBLIC_ID",
        )

        read_functions = "\n".join([function.to_string() for function in self.read_functions])
        contract_py += read_functions

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

    def scaffold_read_function(self, function):
        """
        Scaffold a read function.
        """
        return ReadContractFunction(function)

    def process(self):
        """
        Scaffold the contract and ensure it is written to the file system.
        """
        self.write_abi_to_file()
        self.parse_functions()
        self.update_all()

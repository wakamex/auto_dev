"""
Contract scaffolder.
"""
import os
import shutil
from dataclasses import dataclass

from auto_dev.cli_executor import CommandExecutor
from auto_dev.contracts.block_explorer import BlockExplorer
from auto_dev.contracts.contract import Contract
from auto_dev.utils import isolated_filesystem


@dataclass
class ContractScaffolder:
    """
    Class to scaffold a contract.
    """

    block_explorer: BlockExplorer
    author: str = "eightballer"

    def from_block_explorer(self, address: str, name: str):
        """
        Scaffold a contract from a block explorer.
        """
        abi = self.block_explorer.get_abi(address)
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

        init_cmd = f"aea init --author {self.author} --reset --ipfs --remote".split(" ")
        if not CommandExecutor(init_cmd).execute(verbose=verbose):
            raise ValueError("Failed to initialise agent lib.")

        with isolated_filesystem():
            if not CommandExecutor("aea create myagent".split(" ")).execute(verbose=verbose):
                raise ValueError("Failed to create agent.")
            os.chdir("myagent")
            if not CommandExecutor(f"aea scaffold contract {contract.name}".split(" ")).execute(verbose=verbose):
                raise ValueError("Failed to scaffold contract.")

            if not contract.path.parent.exists():
                contract.path.parent.mkdir(parents=True)
            shutil.copytree(
                f"contracts/{contract.name}",
                contract.path,
            )
        return contract.path

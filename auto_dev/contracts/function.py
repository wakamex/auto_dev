"""
Function class.

"""

from dataclasses import dataclass
from typing import Any, Dict

from auto_dev.contracts.contract_templates import READ_FUNCTION_TEMPLATE
from auto_dev.contracts.utils import from_camel_case_to_snake_case
from auto_dev.contracts.variable import Variable


@dataclass
class Function:
    """
    A function of a contract.
    """

    abi: Dict[str, Any]

    def to_string(self):
        """
        Returns the function as a string.
        """
        spacer = ",\n" + (" " * 8)
        returns = spacer.join([param.to_str_return() for param in self.outputs])
        args = spacer.join([param.to_str_arg() for param in self.inputs])
        params = spacer.join([param.to_str_params() for param in self.inputs])
        return READ_FUNCTION_TEMPLATE.substitute(
            name=self.name if self.name != "" else "constructor", params=params, args=args, returns=returns
        )

    @property
    def name(self):
        """Return the name of the function."""
        return from_camel_case_to_snake_case(self.abi["name"])

    @property
    def inputs(self):
        """Return the inputs as variables."""
        return [Variable(**param) for param in self.abi["inputs"]]

    @property
    def outputs(self):
        """Return the outputs as variables."""
        return [Variable(**param) for param in self.abi["outputs"]]

    @property
    def is_read_only(self):
        """Is the function read only."""
        return self.abi["stateMutability"] == "view"

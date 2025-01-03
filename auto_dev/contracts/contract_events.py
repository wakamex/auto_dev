"""
Class to represent and parse contract events.
"""
from dataclasses import dataclass

from auto_dev.contracts.utils import SOLIDITY_TO_PYTHON_TYPES, keyword_to_safe_name
from auto_dev.contracts.contract_templates import EVENT_TEMPLATE
from auto_dev.contracts.variable import Variable
from auto_dev.utils import camel_to_snake, snake_to_camel



@dataclass
class ContractEvent:
    anonymous: bool
    inputs: list
    name: str
    type: str

    def vars(self):
        """return variable instances for the inputs."""
        return [Variable(**input) for input in self.inputs]

    def to_string(self):
        """Return the event as a string."""
        return EVENT_TEMPLATE.substitute(
            name=camel_to_snake(self.name),
            params=("=None,".join([var.to_str_params() for var in self.vars()])) + "=None",
            args=",".join([var.to_str_arg() for var in self.vars()]),
            python_names=",".join([var.python_name() for var in self.vars()]), 
            keywords=", ".join(v.to_key_value() for v in self.vars()),
            camel_name=self.name,
        )


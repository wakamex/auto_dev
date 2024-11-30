"""
Class to represent and parse contract events.
"""
from dataclasses import dataclass

from auto_dev.contracts.utils import SOLIDITY_TO_PYTHON_TYPES
from auto_dev.contracts.contract_templates import EVENT_TEMPLATE
from auto_dev.utils import camel_to_snake, snake_to_camel

@dataclass
class ContractEvent:
    anonymous: bool
    inputs: list
    name: str
    type: str

    def inputs_list(self):
        """Return the inputs as a string."""
        return ", ".join([input["type"] for input in self.inputs])
    
    def args(self):
        """Return the inputs as a string."""
        return ", ".join([input["name"] for input in self.inputs])

    def inputs_with_types(self):
        """Return the inputs with names."""
        return ", ".join([f"{input['name']}: {SOLIDITY_TO_PYTHON_TYPES[input['type']]} = None" for input in self.inputs])
    

    def to_string(self):
        """Return the event as a string."""
        return EVENT_TEMPLATE.substitute(
            name=camel_to_snake(self.name),
            params=self.inputs_with_types(),
            args=self.args(),
            camel_name=self.name,
        )


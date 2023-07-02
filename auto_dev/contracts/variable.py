"""
This module contains the Variable class.
"""
from dataclasses import dataclass
from typing import Any, Optional

from auto_dev.contracts.param_type import ParamType
from auto_dev.contracts.utils import PARAM_TO_STR_MAPPING


@dataclass
class Variable:
    """This class represent a variable in solidity."""

    internalType: ParamType  # pylint: disable=C0103
    type: ParamType
    name: str
    components: Optional[Any] = None

    def to_str_params(self):
        """Parse the variable to string to be passed as a parameter to a function."""
        return f"{self._name}: {self.python_type}"

    def to_str_arg(self):
        """Parse the variable to string to be passed as an argument to a function."""
        return f"{self._name}={self.name}"

    def to_str_return(self):
        """Parse the variable to string to be returned by a function."""
        result_name = self.name if self.name != "" else self.python_type.lower()
        return f"'{result_name}': result"

    @property
    def _name(self):
        """Return the name of the variable."""
        if self.name == "":
            return "constructor"
        return self.name

    @property
    def solidity_type(self):
        """Return the solidity type of the variable."""
        try:
            return ParamType(self.internalType)
        except ValueError:
            return ParamType(self.type)

    @property
    def python_type(self):
        """Return the python type of the variable."""
        return PARAM_TO_STR_MAPPING[self.solidity_type]

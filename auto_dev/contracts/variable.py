"""Module contains the Variable class."""

from typing import Any
from dataclasses import dataclass

from auto_dev.contracts.utils import PARAM_TO_STR_MAPPING
from auto_dev.contracts.param_type import ParamType


@dataclass
class Variable:
    """This class represent a variable in solidity."""

    type: ParamType
    name: str
    internalType: ParamType = None  # noqa
    components: Any | None = None
    index: int | None = None

    def to_str_params(self) -> str:
        """Parse the variable to string to be passed as a parameter to a function."""
        return f"{self._name}: {self.python_type}"

    def to_str_arg(self) -> str:
        """Parse the variable to string to be passed as an argument to a function."""
        if self.name == "":
            return f"{self._name}"
        return f"{self._name}={self._name}"

    def to_str_return(self) -> str:
        """Parse the variable to string to be returned by a function."""
        result_name = self.name if self.name != "" else self.python_type.lower()
        return f"'{result_name}': result"

    @property
    def _name(self):
        """Return the name of the variable."""
        if self.name == "":
            return f"var_{self.index}"
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

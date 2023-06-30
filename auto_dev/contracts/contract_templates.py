"""
Contains the necessary templates for the contracts
"""
from dataclasses import dataclass
from enum import Enum
from string import Template
from typing import Any, Dict

from aea.crypto.base import Address

from auto_dev.data.contracts.header import HEADER as CONTRACT_HEADER
from auto_dev.data.contracts.header import IMPORTS as CONTRACT_IMPORTS

PUBLIC_ID = Template(
    """
PUBLIC_ID = PublicId.from_str("$AUTHOR/$NAME:0.1.0")
"""
)

# pylint: disable=W1401
CONTRACT_TEMPLATE = Template(
    """
$HEADER

\"""$NAME contract\"""

$CONTRACT_IMPORTS

$PUBLIC_ID

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class $NAME\Contract(Contract):
    \"\"\"The $NAME contract class.\"\"\"

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        \"\"\"Get raw transaction.\"\"\"
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        \"\"\"Get raw message.\"\"\"
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        \"\"\"Get state.\"\"\"
        raise NotImplementedError

    @classmethod
    def get_deploy_transaction(
        cls, ledger_api: LedgerApi, deployer_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        \"\"\"Get deploy transaction.\"\"\"
        Get deploy transaction.

        :param ledger_api: ledger API object.
        :param deployer_address: the deployer address.
        :param kwargs: the keyword arguments.
        :return: an optional JSON-like object.
        \"\"\"
        return super().get_deploy_transaction(ledger_api, deployer_address, **kwargs)
$READ_ONLY_FUNCTIONS
$WRITE_FUNCTIONS
"""
)


class ParamType(Enum):
    """This class represent the type of a parameter in solidity."""

    ADDRESS = "address"
    BOOL = "bool"
    UINT256 = "uint256"
    INT128 = "int128"


@dataclass
class Variable:
    """This class represent a variable in solidity."""

    internalType: ParamType  # pylint: disable=C0103
    type: ParamType
    name: str

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
        raise ValueError("The name of the variable is not set.")

    @property
    def solidity_type(self):
        """Return the solidity type of the variable."""
        return ParamType(self.internalType)

    @property
    def python_type(self):
        """Return the python type of the variable."""
        return param_to_str_mapping[self.solidity_type]


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
        template = Template(
            """
    @classmethod
    def $name(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        $params
        ) -> Optional[JSONLike]:
        \"\"\"Handler method for the '$name' requests.\"\"\"
        instance = cls.get_instance(ledger_api, contract_address)
        result = instance.$name($args).call()
        return {
            $returns
        }

        """
        )
        spacer = ",\n" + (" " * 8)
        returns = spacer.join([param.to_str_return() for param in self.outputs])
        args = spacer.join([param.to_str_arg() for param in self.inputs])
        params = spacer.join([param.to_str_params() for param in self.inputs])
        return template.substitute(
            name=self.name if self.name != "" else "constructor", params=params, args=args, returns=returns
        )

    @property
    def name(self):
        """Return the name of the function."""
        return self.abi["name"]

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


solidity_type_to_python_type = {
    "address": Address,
    "bool": bool,
    "uint256": int,
    "int128": int,
}


param_to_str_mapping = {
    ParamType.ADDRESS: "Address",
    ParamType.BOOL: "bool",
    ParamType.UINT256: "int",
    ParamType.INT128: "int",
}


READ_TEST_CASES = [
    {
        'inputs': [],
        'name': 'admin',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': 'comptrollerImplementation',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': 'pendingAdmin',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': 'pendingComptrollerImplementation',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
]

WRITE_TEST_CASES = [
    {
        'inputs': [],
        'name': '_acceptAdmin',
        'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': '_acceptImplementation',
        'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'inputs': [{'internalType': 'address', 'name': 'newPendingAdmin', 'type': 'address'}],
        'name': '_setPendingAdmin',
        'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'inputs': [{'internalType': 'address', 'name': 'newPendingImplementation', 'type': 'address'}],
        'name': '_setPendingImplementation',
        'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'inputs': [{'internalType': 'address', 'name': '_admin', 'type': 'address'}],
        'name': 'setAdmin',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
]

test_cases = [
    {
        'inputs': [],
        'name': 'admin',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': 'comptrollerImplementation',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': 'pendingAdmin',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': 'pendingComptrollerImplementation',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
]

args = {
    "HEADER": CONTRACT_HEADER,
    "CONTRACT_IMPORTS": CONTRACT_IMPORTS,
    # vars
    "NAME": "MyContract",
    "AUTHOR": "MyAuthor",
    "READ_ONLY_FUNCTIONS": READ_TEST_CASES,
    "WRITE_FUNCTIONS": "",
}


def main(args):
    """Run the main script."""
    public_id = PUBLIC_ID.substitute(args)
    args["PUBLIC_ID"] = public_id

    # we first need to parse the read only functions and generate the corresponding tests
    read_functions = []
    for read_only_function in args["READ_ONLY_FUNCTIONS"]:
        func = Function(read_only_function)
        read_functions.append(func.to_string())

    args["READ_ONLY_FUNCTIONS"] = "\n".join(read_functions)

    result = CONTRACT_TEMPLATE.substitute(args)
    print(result)

    # we next need to parse the write functions and generate the corresponding tests


if __name__ == "__main__":
    main(args)

"""
Contains the necessary templates for the contracts
"""
from string import Template

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


READ_FUNCTION_TEMPLATE: Template = Template(
    """
    @classmethod
    def $name(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        $params
        ) -> JSONLike:
        \"\"\"Handler method for the '$name' requests.\"\"\"
        instance = cls.get_instance(ledger_api, contract_address)
        result = instance.$name($args).call()
        return {
            $returns
        }

"""
)


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

    args["READ_ONLY_FUNCTIONS"] = "\n".join(read_functions)

    result = CONTRACT_TEMPLATE.substitute(args)
    print(result)

    # we next need to parse the write functions and generate the corresponding tests


if __name__ == "__main__":
    main(args)

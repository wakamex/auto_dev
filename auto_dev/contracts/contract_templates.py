"""
Contains the necessary templates for the contracts


        
"""
from auto_dev.data.contracts.header import header as CONTRACT_HEADER
from auto_dev.data.contracts.header import imports as CONTRACT_IMPORTS

from string import Template

from dataclasses import dataclass


PUBLIC_ID = Template("""
PUBLIC_ID = PublicId.from_str("$AUTHOR/$NAME:0.1.0")
""")

CONTRACT_TEMPLATE = Template("""
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
""")


    # @classmethod
    # def get_transmit_data(
    #     cls,
    #     ledger_api: EthereumApi,
    #     contract_address: str,
    #     epoch_: int,
    #     round_: int,
    #     amount_: int,
    # ) -> JSONLike:
    #     """
    #     Handler method for the 'get_active_project' requests.

    #     Implement this method in the sub class if you want
    #     to handle the contract requests manually.

    #     :param ledger_api: the ledger apis.
    #     :param contract_address: the contract address.
    #     :param epoch_: the epoch
    #     :param round_: the round
    #     :param amount_: the amount
    #     :return: the tx  # noqa: DAR202
    #     """
    #     instance = cls.get_instance(ledger_api, contract_address)
    #     report = cls.get_report(epoch_, round_, amount_)
    #     data = instance.encodeABI(fn_name="transmit", args=[report])
    #     return {"data": bytes.fromhex(data[2:])}  # type: ignore

    # @classmethod
    # def transmit(  # pylint: disable=too-many-arguments
    #     cls,
    #     ledger_api: EthereumApi,
    #     contract_address: str,
    #     epoch_: int,
    #     round_: int,
    #     amount_: int,
    #     **kwargs: Any,
    # ) -> Optional[JSONLike]:
    #     """
    #     Handler method for the 'get_active_project' requests.

    #     Implement this method in the sub class if you want
    #     to handle the contract requests manually.

    #     :param ledger_api: the ledger apis.
    #     :param contract_address: the contract address.
    #     :param epoch_: the epoch
    #     :param round_: the round
    #     :param amount_: the amount
    #     :param kwargs: the kwargs
    #     :return: the tx  # noqa: DAR202
    #     """
    #     contract_instance = cls.get_instance(ledger_api, contract_address)
    #     report = cls.get_report(epoch_, round_, amount_)

    #     return ledger_api.build_transaction(
    #         contract_instance=contract_instance,
    #         method_name="transmit",
    #         method_args={"_report": report},
    #         tx_args=kwargs,
    #     )


args = {
    "HEADER": CONTRACT_HEADER,
    "CONTRACT_IMPORTS": CONTRACT_IMPORTS,
    # vars
    "NAME": "MyContract",
    "AUTHOR": "MyAuthor",
    "READ_ONLY_FUNCTIONS": "READ_ONLY_FUNCTIONS",
    "WRITE_FUNCTIONS": "WRITE_FUNCTIONS",

}

def main(args):
    public_id = PUBLIC_ID.substitute(args)
    print(public_id)
    args["PUBLIC_ID"] = public_id

    result = CONTRACT_TEMPLATE.substitute(args)
    print(result)



if __name__ == "__main__":
    main(args)

# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 eightballer
#   Copyright 2021-2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""The tests module contains the tests of the packages/contracts/orca_whirlpool dir."""
# type: ignore # noqa: E800
# pylint: skip-file

import json
from pathlib import Path
from typing import cast

from aea_ledger_ethereum import EthereumApi
import pytest
from aea.configurations.loader import (
    ComponentType,
    ContractConfig,
    load_component_configuration,
)
from aea.contracts.base import Contract, contract_registry
from aea_ledger_solana import SolanaApi, SolanaCrypto

from packages.eightballer.contracts.erc_20.contract import Erc20

PACKAGE_DIR = Path(__file__).parent/ "packages" / "eightballer" / "contracts" / "erc_20"

DEFAULT_ADDRESS = "https://rpc.ankr.com/base"

CONTRACT_ADDRESS = "0x42156841253f428cb644ea1230d4fddfb70f8891"


class TestContractCommon:
    """Other tests for the contract."""

    @classmethod
    def setup(cls) -> None:
        """Setup."""

        # Register smart contract used for testing
        cls.path_to_contract = PACKAGE_DIR

        # register contract
        configuration = cast(
            ContractConfig,
            load_component_configuration(ComponentType.CONTRACT, cls.path_to_contract, skip_consistency_check=True),
        )
        configuration._directory = (  # pylint: disable=protected-access
            cls.path_to_contract
        )
        if str(configuration.public_id) not in contract_registry.specs:
            # load contract into sys modules
            Contract.from_config(configuration)
        cls.contract = contract_registry.make(str(configuration.public_id))

        CONFIG = {
            "address": DEFAULT_ADDRESS,
        }
        cls.ledger_api = EthereumApi(**CONFIG)

    def test_get_transfer_events(self, ):
        """Test the get_token method."""

        token_data = self.contract.get_hearted_events(self.ledger_api, 
                                                       contract_address=CONTRACT_ADDRESS,
                                                       look_back=1000000,
                                                       )

        meme_token = '0x7484a9fB40b16c4DFE9195Da399e808aa45E9BB9'
        filtered = [f for f in token_data['events'] if f['args']['memeToken'] == meme_token]

        headers = ['blockNumber', 'transactionHash', 'hearter', 'memeToken', 'amount']

        output = [headers]

        for event in filtered:
            row = [event['blockNumber'], event['transactionHash'].hex(), event['args']['hearter'], event['args']['memeToken'], event['args']['amount']]
            output.append(row)



        import csv

        with open('hearted.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(output)
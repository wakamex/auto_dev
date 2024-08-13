"""Module to interact with the blockchain explorer."""

import json
from dataclasses import dataclass

import requests
from web3 import Web3

from auto_dev.constants import DEFAULT_TIMEOUT


@dataclass
class BlockExplorer:
    """Class to interact with the blockchain explorer."""

    url: str
    api_key: str = None

    def _authenticated_request(self, url: str, params: dict | None = None):
        """Make an authenticated request.
        The api key is encoded into the url.
        """
        if not params:
            params = {}
        params["apiKey"] = self.api_key
        return requests.get(
            url,
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )

    def get_abi(self, address: str):
        """Get the abi for the contract at the address."""
        web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        check_address = web3.to_checksum_address(address)
        url = self.url + "/api?module=contract&action=getabi&address=" + str(check_address)
        response = self._authenticated_request(url)
        if response.status_code != 200:
            msg = f"Failed to get abi with api response error result `{response.status_code}`"
            raise ValueError(msg)
        if response.json()["status"] != "1":
            msg = f"Failed to get abi for address {address} with status {response.json()['result']}"
            raise ValueError(msg)
        if response.status_code != 200:
            msg = f"Failed to get abi with api response error result `{response.status_code}`"
            raise ValueError(msg)
        return json.loads(response.json()["result"])

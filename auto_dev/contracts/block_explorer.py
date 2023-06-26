"""
Module to interact with the blockchain explorer.
"""

from dataclasses import dataclass
import json

import requests


from auto_dev.constants import DEFAULT_TIMEOUT


@dataclass
class BlockExplorer:
    """
    Class to interact with the blockchain explorer.
    """

    url: str
    api_key: str = None

    def _authenticated_request(self, url: str, params: dict = None):
        """
        Make an authenticated request.
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
        """
        Get the abi for the contract at the address.
        """
        url = self.url + "/api?module=contract&action=getabi&address=" + address
        response = self._authenticated_request(url)
        if response.status_code != 200:
            raise ValueError(f"Failed to get abi for address {address} with status code {response.status_code}")
        return json.loads(response.json()['result'])


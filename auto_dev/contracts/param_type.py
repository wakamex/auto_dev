"""
This module contains the ParamType class, which represents the type of a parameter in solidity.
"""
from enum import Enum


class ParamType(Enum):
    """This class represent the type of a parameter in solidity."""

    ADDRESS = "address"
    BOOL = "bool"
    UINT256 = "uint256"
    UNINT64 = "uint64"
    UINT8 = "uint8"
    INT128 = "int128"
    INT256 = "int256"
    BYTES32 = "bytes32"
    UINT80 = "uint80"
    TUPLE = "tuple"
    UINT256_ARRAY = "uint256[]"
    ADDRESS_ARRAY = "address[]"
    STRING = "string"

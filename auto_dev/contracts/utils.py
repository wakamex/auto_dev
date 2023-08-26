"""
Utils for the contracts.
"""

from aea.crypto.base import Address

from auto_dev.contracts.param_type import ParamType


def from_snake_case_to_camel_case(string: str):
    """
    Convert a string from snake case to camel case.
    """
    return "".join(word.capitalize() for word in string.split("_"))


def from_camel_case_to_snake_case(string: str):
    """
    Convert a string from camel case to snake case.
    Note: If the string is all uppercase, it will be converted to lowercase.
    """
    if string.isupper():
        return string.lower()
    return "".join("_" + c.lower() if c.isupper() else c for c in string).lstrip("_")


SOLIDITY_TYPE_TO_PYTHON_TYPE = {
    "address": Address,
    "bool": bool,
    "uint256": int,
    "int128": int,
}

SOLIDITY_TO_PYTHON_TYPES = {
    "address": "str",
    "bool": "bool",
    "bytes32": "str",
    "bytes4": "str",
    "bytes": "str",
    "uint256": "int",
    "uint80": "int",
    "int8": "int",
    "tuple": "tuple",
    "int16": "int",
}


PARAM_TO_STR_MAPPING = {
    ParamType.ADDRESS: "Address",
    ParamType.BOOL: "bool",
    ParamType.BYTES32: "str",
    ParamType.BYTES4: "str",
    ParamType.BYTES: "str",
    ParamType.UINT256: "int",
    ParamType.INT128: "int",
    ParamType.UINT80: "int",
    ParamType.TUPLE: "tuple",
    ParamType.UINT256_ARRAY: "List[int]",
    ParamType.UNINT64: "int",
    ParamType.UINT8: "int",
    ParamType.INT256: "int",
    ParamType.ADDRESS_ARRAY: "List[Address]",
    ParamType.STRING: "str",
    ParamType.UINT128: "int",
    ParamType.UINT24: "int",
    ParamType.INT24: "int",
    ParamType.UINT16: "int",
    ParamType.INT80_ARRAY: "List[int]",
    ParamType.UINT64_ARRAY: "List[int]",
    ParamType.TUPLE_ARRAY: "Tuple[...]",
    ParamType.UINT32_ARRAY: "List[int]",
    ParamType.INT16: "int",
}

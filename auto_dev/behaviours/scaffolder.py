"""Protocol scaffolder."""

import re
import ast
import datetime
import tempfile
import textwrap
import subprocess
from typing import Any
from pathlib import Path
from itertools import starmap
from collections import namedtuple

import yaml
from jinja2 import Environment, FileSystemLoader
from aea.protocols.generator.base import ProtocolGenerator

from auto_dev.fmt import Formatter
from auto_dev.utils import currenttz, get_logger, remove_prefix, camel_to_snake, snake_to_camel
from auto_dev.constants import DEFAULT_TZ, DEFAULT_ENCODING, JINJA_TEMPLATE_FOLDER
from auto_dev.exceptions import UserInputError
from auto_dev.protocols.scaffolder import PROTOBUF_TO_PYTHON, ProtocolScaffolder, read_protocol, parse_protobuf_type
from auto_dev.data.connections.template import HEADER


ProtocolSpecification = namedtuple("ProtocolSpecification", ["metadata", "custom_types", "speech_acts"])


README_TEMPLATE = """
# {name} Protocol

## Description

...

## Specification

```yaml
{protocol_definition}
```
"""

DEFAULT_TARGET_CONNECTION = "eightballer/docker_engine:0.1.0"


DEFAULT_TYPE_MAP = {
    "str": "'string-type'",
    "int": 8,
    "float": 8.8,
    "bool": False,
    "Dict": {},
    "List": [],
    "Optional": None,
    "Tuple": (),
}


PYTHHON_KEYWORDS = [
    "None",
    "False",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "also",
    "all",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
    "print",
    "abs",
    "delattr",
    "hash",
    "memoryview",
    "set",
    "all",
    "dict",
    "max",
]


class BehaviourScaffolder(ProtocolScaffolder):
    """ProtocolScaffolder."""

    component_class: str = "behaviours"
    type: str = None

    def __init__(
        self, protocol_specification_path: str, behaviour_type, logger, verbose: bool = True, auto_confirm: bool = False
    ):
        """Initialize ProtocolScaffolder."""
        self.logger = logger or get_logger()
        self.verbose = verbose
        self.behaviour_type = behaviour_type
        self.protocol_specification_path = protocol_specification_path
        self.logger.info(f"Read protocol specification: {protocol_specification_path}")
        self.auto_confirm = auto_confirm
        self.env = Environment(loader=FileSystemLoader(JINJA_TEMPLATE_FOLDER), autoescape=False)

    def scaffold(self, target_speech_acts=None) -> None:
        """Scaffold the protocol."""
        template = self.env.get_template(str(Path(self.component_class) / f"{self.behaviour_type.value}.jinja"))
        protocol_specification = read_protocol(self.protocol_specification_path)
        raw_classes, all_dummy_data, enums = self._get_definition_of_custom_types(protocol=protocol_specification)

        speech_acts = protocol_specification.metadata["speech_acts"]

        type_mapp = {}
        for type in protocol_specification.custom_types:
            self.logger.info(f"Type: {type}")
            type_mapp[type] = type[3:]
        # We then collect the speech acts
        # print(raw_classes)

        if not target_speech_acts:
            target_speech_acts = speech_acts.keys()
        else:
            target_speech_acts = target_speech_acts.split(",")
            failures = []
            for target in target_speech_acts:
                if target not in speech_acts:
                    failures.append(target)
            if failures:
                raise UserInputError(
                    textwrap.dedent(f"""
                    Speech act {target} not found in the protocol specification. 
                    Available: {list(speech_acts.keys())}
                    """)
                )
        parsed_speech_acts = {}
        for speech_act, data in speech_acts.items():
            if speech_act not in target_speech_acts:
                continue
            default_kwargs = {}
            for arg, arg_type in data.items():
                if arg in PYTHHON_KEYWORDS:
                    self.logger.info(f"Arg: {arg} is a python keyword")
                    py_arg = f"{arg}_"
                else:
                    py_arg = arg
                py_type = (
                    arg_type.replace("pt:str", "str")
                    .replace("pt:int", "int")
                    .replace("pt:float", "float")
                    .replace("pt:bool", "bool")
                )
                py_type = (
                    py_type.replace("pt:dict", "Dict")
                    .replace("pt:list", "List")
                    .replace("pt:optional", "Optional")
                    .replace("pt:tuple", "Tuple")
                )
                for ct, pt in type_mapp.items():
                    py_type = py_type.replace(ct, pt)
                if py_type not in DEFAULT_TYPE_MAP:
                    if py_type.startswith("Optional"):
                        DEFAULT_TYPE_MAP[py_type] = None
                    else:
                        raise ValueError(f"Type {py_type} not found in the default type map.")

                default_kwargs[arg] = (py_type, DEFAULT_TYPE_MAP[py_type], py_arg)
            parsed_speech_acts[speech_act] = default_kwargs

        print(parsed_speech_acts)
        output = template.render(
            protocol_name=protocol_specification.metadata["name"],
            author=protocol_specification.metadata["author"],
            year=datetime.datetime.now(currenttz()).year,
            raw_classes=raw_classes,
            all_dummy_data=all_dummy_data,
            enums=enums,
            class_name=snake_to_camel(protocol_specification.metadata["name"]),
            speech_acts=parsed_speech_acts,
            target_connection=DEFAULT_TARGET_CONNECTION,
        )
        # We first collect the custom types
        if self.verbose:
            self.logger.info(f"Generated output: {output}")

        print(output)

    def get_data_types(self, protocol_specification: ProtocolSpecification) -> str:
        """Get the data types."""
        data_types = protocol_specification.custom_types
        return data_types

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
from auto_dev.utils import currenttz, get_logger, remove_prefix, camel_to_snake
from auto_dev.constants import DEFAULT_TZ, DEFAULT_ENCODING, JINJA_TEMPLATE_FOLDER
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


class BehaviourScaffolder:
    """ProtocolScaffolder."""

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
        self.env = Environment(loader=FileSystemLoader(JINJA_TEMPLATE_FOLDER), autoescape=True)

    def scaffold(self) -> None:
        """Scaffold the protocol."""
        self.protocol_specification = self._load_protocol_specification()
        template = self.env.get_template("test_custom.jinja")
        output = template.render(
            name="test",
        )
        if self.verbose:
            self.logger.info(f"Generated output: {output}")

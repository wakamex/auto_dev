"""Protocol scaffolder."""

import subprocess
import tempfile
from collections import namedtuple
from pathlib import Path
from typing import Dict

import re
from itertools import starmap
import yaml
from aea.protocols.generator.base import ProtocolGenerator

from auto_dev.commands.fmt import Formatter
from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.utils import get_logger, remove_prefix, camel_to_snake

ProtocolSpecification = namedtuple('ProtocolSpecification', ['metadata', 'custom_types', 'speech_acts'])


README_TEMPLATE = """
# {name} Protocol

## Description

...

## Specification

```yaml
{protocol_definition}
```
"""


def read_protocol(filepath: str) -> ProtocolSpecification:
    """Read protocol specification."""

    content = Path(filepath).read_text(encoding=DEFAULT_ENCODING)
    if "```" in content:
        if content.count("```") != 2:
            raise ValueError("Expecting a single code block")
        content = remove_prefix(content.split('```')[1], "yaml")

    # use ProtocolGenerator to validate the specification
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        Path(temp_file.name).write_text(content, encoding=DEFAULT_ENCODING)
        ProtocolGenerator(temp_file.name)

    metadata, custom_types, speech_acts = yaml.safe_load_all(content)
    return ProtocolSpecification(metadata, custom_types, speech_acts)


def parse_enums(protocol: ProtocolSpecification) -> Dict[str, Dict[str, str]]:
    enums = {}
    for ct_name, definition in protocol.custom_types.items():
        if not definition.startswith("enum "):
            continue
        result = re.search(r'\{([^}]*)\}', definition)
        if not result:
            raise ValueError(f"Error parsing enum fields from: {definition}")
        fields = {}
        for enum in filter(None, result.group(1).strip().split(";")):
            name, number = enum.split("=")
            fields[name.strip()] = number.strip()
        enums[ct_name[3:]] = fields
    return enums


class EnumModifier:
    """EnumModifier"""

    def __init__(self, protocol_path: Path, logger):
        """"""

        self.protocol_path = protocol_path
        self.protocol = read_protocol(protocol_path / "README.md")
        self.logger = logger

    def augment_enums(self):
        enums = parse_enums(self.protocol)
        if not enums:
            return

        custom_types_path = self.protocol_path / "custom_types.py"
        content = custom_types_path.read_text()


class ProtocolScaffolder:
    """ProtocolScaffolder"""

    def __init__(self, protocol_specification_path: str, language, logger, verbose: bool = True):
        """Initialize ProtocolScaffolder."""

        self.logger = logger or get_logger()
        self.verbose = verbose
        self.language = language
        self.protocol_specification_path = protocol_specification_path
        self.logger.info(f"Read protocol specification: {protocol_specification_path}")

    def generate(self) -> None:
        """Generate protocol."""

        command = f"aea generate protocol {self.protocol_specification_path} --l {self.language}"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if not result.returncode == 0:
            raise ValueError(f"Protocol scaffolding failed: {result.stderr}")

        protocol = read_protocol(self.protocol_specification_path)
        protocol_author = protocol.metadata["author"]
        protocol_name = protocol.metadata["name"]
        protocol_version = protocol.metadata["version"]

        protocol_path = Path.cwd() / "protocols" / protocol_name

        readme = protocol_path / "README.md"
        protocol_definition = Path(self.protocol_specification_path).read_text(encoding=DEFAULT_ENCODING)
        kwargs = {
            "name": " ".join(map(str.capitalize, protocol_name.split("_"))),
            "protocol_definition": protocol_definition,
        }
        content = README_TEMPLATE.format(**kwargs)
        readme.write_text(content.strip(), encoding=DEFAULT_ENCODING)

        EnumModifier(protocol_path, self.logger).augment_enums()

        command = f"aea fingerprint protocol {protocol_author}/{protocol_name}:{protocol_version}"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if not result.returncode == 0:
            raise ValueError(f"Protocol fingerprinting failed: {result.stderr}")

        protocol_path = Path.cwd() / "protocols" / protocol_name
        self.logger.info(f"New protocol scaffolded at {protocol_path}")

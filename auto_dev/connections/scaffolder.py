import sys
import tempfile
from collections import namedtuple
from pathlib import Path
import yaml
import shutil
import tempfile
from auto_dev.cli_executor import CommandExecutor
from aea.protocols.generator.base import ProtocolGenerator
from aea import AEA_DIR

from auto_dev.utils import folder_swapper, get_logger
from auto_dev.constants import AEA_CONFIG
from auto_dev.data.connections.template import CONNECTION_TEMPLATE
from auto_dev.data.connections.test_template import TEST_CONNECTION_TEMPLATE


ProtocolSpecification = namedtuple('ProtocolSpecification', ['metadata', 'custom_types', 'speech_acts'])


def to_camel(s: str, sep="") -> str:
    """Snake to camelcase."""
    return sep.join(map(str.capitalize, s.split("_")))


def read_protocol(filepath: str) -> ProtocolSpecification:
    """Read protocol specification."""

    content = Path(filepath).read_text()
    if "```" in content:
        if content.count("```") != 2:
            raise ValueError("Expecting a single code block")
        content = content.split('```')[1].lstrip("yaml")  # TODO: use remove_prefix

    # use ProtocolGenerator to validate the specification
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        Path(temp_file.name).write_text(content)
        ProtocolGenerator(temp_file.name)

    metadata, custom_types, speech_acts = yaml.safe_load_all(content)
    return ProtocolSpecification(metadata, custom_types, speech_acts)


class ConnectionFolderTemplate:
    """ConnectionFolderTemplate"""

    def __init__(self, logger, protocol):
        """"""
        self.logger = logger
        self.src = Path(AEA_DIR) / "connections" / "scaffold"
        self.path = Path(tempfile.mkdtemp()) / "scaffold"
        self.protocol = protocol
        shutil.copytree(self.src, self.path)

        self.readme = (self.path / "readme.md").read_text()
        self.connection = self.path / "connection.py"
        self.yaml = yaml.safe_load_all(self.path / "connection.yaml")
        self.tests = self.path / "tests"
        self.test_connection = self.tests / "test_connection.py"

    @property
    def kwargs(self) -> dict:
        name = "test_connection"

        protocol_name = self.protocol.metadata["name"]
        protocol_author = self.protocol.metadata["author"]
        speech_acts = list(self.protocol.metadata["speech_acts"])
        roles = list(self.protocol.speech_acts["roles"])  # TODO rename

        kwargs = {
            "year": 2023,  # overwritten by aea scaffold
            "author": AEA_CONFIG["author"],  # overwritten by aea scaffold in copyright header
            "name": name,
            "name_camelcase": to_camel(name),
            "proper_name": to_camel(name, sep=" "),
            "protocol_author": protocol_author,
            "protocol_name": protocol_name,
            "protocol_name_camelcase": to_camel(protocol_name),
            "ROLE": roles[0].upper(),
            "OTHER_ROLE": roles[-1].upper(),
            "PERFORMATIVE": speech_acts[0].upper(),
        }

        return kwargs

    def augment(self) -> None:
        """(Over)write the connection files."""

        self.tests.mkdir()
        (self.tests / "__init__.py").touch()
        
        doc = "".join(part.format(**self.kwargs) + "\n" for part in CONNECTION_TEMPLATE)
        self.connection.write_text(doc)

        doc = "".join(part.format(**self.kwargs) + "\n" for part in TEST_CONNECTION_TEMPLATE)
        self.test_connection.write_text(doc)


class ConnectionScaffolder:
    """ConnectionScaffolder"""

    def __init__(self, name, protocol, logger, verbose: bool = True):
        """Initialize ConnectionScaffolder."""

        self.name = name
        self.logger = logger or get_logger()
        self.verbose = verbose
        self.protocol = protocol
        if self.protocol:
            self.protocol = read_protocol(protocol)
            self.logger.info(f"Read protocol specification: {protocol}")

    def generate(self) -> None:
        """Generate connection."""

        template = ConnectionFolderTemplate(self.logger, self.protocol)
        template.augment()

        with folder_swapper(template.path, template.src):
            command = f"aea scaffold connection {self.name}"
            cli_executor = CommandExecutor(command.split(" "))
            result = cli_executor.execute(verbose=self.verbose)
            if not result:
                self.logger.error(f"Command failed: {command}")
                sys.exit(1)

   
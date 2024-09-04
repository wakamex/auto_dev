"""Constants for the auto_dev package."""

import os
from enum import Enum
from pathlib import Path

from aea.cli.utils.config import get_or_create_cli_config


DEFAULT_ENCODING = "utf-8"
DEFAULT_TZ = "UTC"
DEFAULT_TIMEOUT = 10
# package directory
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RUFF_CONFIG = Path(PACKAGE_DIR) / "data" / "ruff.toml"
AUTONOMY_PACKAGES_FILE = "packages/packages.json"
AUTO_DEV_FOLDER = os.path.join(os.path.dirname(__file__))
PLUGIN_FOLDER = os.path.join(AUTO_DEV_FOLDER, "commands")
TEMPLATE_FOLDER = os.path.join(AUTO_DEV_FOLDER, "data", "repo", "templates")
JINJA_TEMPLATE_FOLDER = os.path.join(AUTO_DEV_FOLDER, "data", "templates",)

AEA_CONFIG = get_or_create_cli_config()

SAMPLE_PACKAGES_JSON = {
    "packages/packages.json": """
{
    "dev": {
        "agent/eightballer/tmp/aea-config.yaml": "bafybeiaa3jynk3bx4uged6wye7pddkpbyr2t7avzze475vkyu2bbjeddrm"
    },
    "third_party": {
    }
}
"""
}

SAMPLE_PACKAGE_FILE = {
    "packages/eightballer/agents/tmp/aea-config.yaml": """
agent_name: tmp
author: eightballer
version: 0.1.0
license: Apache-2.0
description: ''
aea_version: '>=1.35.0, <2.0.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections: []
contracts: []
protocols:
- open_aea/signing:1.0.0:bafybeibqlfmikg5hk4phzak6gqzhpkt6akckx7xppbp53mvwt6r73h7tk4
skills: []
default_connection: null
default_ledger: ethereum
required_ledgers:
- ethereum
default_routing: {}
connection_private_key_paths: {}
private_key_paths: {}
logging_config:
  disable_existing_loggers: false
  version: 1
dependencies:
  open-aea-ledger-ethereum: {}
"""
}


SAMPLE_PYTHON_CLI_FILE = """
\"\"\"CLI for {project_name}.\"\"\"

import click

from {project_name}.main import main


@click.command()
def cli():
    \"\"\"CLI entrypoint for the {project_name} module.\"\"\"
    main()
"""


SAMPLE_PYTHON_MAIN_FILE = """
\"\"\"Main module for {project_name}.\"\"\"

def main():
    \"\"\"Main entrypoint for the {project_name} module.\"\"\"
    print("Hello World")

"""

BASE_FSM_SKILLS = {
    "registration_abci": "bafybeib6fsfur5jnflcveidnaeylneybwazewufzwa5twnwovdqgwtwsxm",
    "reset_pause_abci": "bafybeibqz7y3i4aepuprhijwdydkcsbqjtpeea6gdzpp5fgc6abrvjz25a",
    "termination_abci": "bafybeieb3gnvjxxsh73g67m7rivzknwb63xu4qeagpkv7f4mqz33ecikem",
}


class FileType(Enum):
    """File type enum."""

    TEXT = "text"
    YAML = "yaml"
    JSON = "json"


class CheckResult(Enum):
    """Check result enum."""

    PASS = "PASS"
    FAIL = "FAIL"
    MODIFIED = "MODIFIED"
    SKIPPED = "SKIPPED"

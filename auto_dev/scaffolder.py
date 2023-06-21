"""
Implement scaffolding tooling
"""

import json
from auto_dev.utils import get_logger


import rich_click as click

logger = get_logger()

# we have a scaffold command group
@click.group()
def scaffold():
    """Scaffolding tooling."""


# we scaffold logging into the agent config.

"""
logging_config:
  disable_existing_loggers: true
  version: 1
  formatters:
    standard:
      format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  handlers:
    http:
      class: logging.handlers.HTTPHandler
      formatter: standard
      level: INFO
      host: localhost:8000
      url: /log/
      method: POST
    console:
      class: rich.logging.RichHandler
      level: DEBUG
  loggers:
    aea:
      handlers:
      - http
      - console
      level: INFO
      propagate: false
"""
import yaml

BASE_LOGGING_CONFIG = yaml.safe_load("""
logging_config:
    disable_existing_loggers: true
    version: 1
    formatters:
        standard:
            format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    handlers:
        {handlers_config}
    loggers:
        aea:
            handlers: {handlers_list}
            level: INFO
            propagate: false
""")

CONSOLE_HANDLER = yaml.safe_load("""
console:
    class: rich.logging.RichHandler
    level: DEBUG
""")

HTTP_HANDLER = yaml.safe_load("""
http:
    class: logging.handlers.HTTPHandler
    formatter: standard
    level: INFO
    host: localhost:8000
    url: /log/
    method: POST
""")


HANDLERS = {
    "console": CONSOLE_HANDLER,
    "http": HTTP_HANDLER,
}

from copy import deepcopy


class Scaffolder:
    """Base scaffolder."""

    def write(self, path: str, content: str):
        """Write the content to the path."""
        with open(path, "w") as file:
            file.write(content)
    

from aea.cli.scaffold import scaffold

class LoggingScaffolder(Scaffolder):
    """Logging scaffolder."""

    def __init__(self):
        """Init scaffolder."""
        self.logger = get_logger()

    def generate(self, handlers: list):
        """Scaffold logging."""
        if not handlers:
            self.logger.error("No handlers provided")
            return
        if handlers == ["all"]:
            handlers = HANDLERS

        else:
            for handler in handlers:
                if handler not in HANDLERS:
                    self.logger.error("Handler '%s' not found", handler)
                    return
                handlers = {
                    handler: HANDLERS[handler] for handler in handlers
                }
        logging_config = deepcopy(BASE_LOGGING_CONFIG)
        logging_config["logging_config"]["handlers"] = handlers
        logging_config["logging_config"]["loggers"]["aea"]["handlers"] = list(handlers.keys())
        return logging_config
    
    def scaffold(self, handlers: list):
        """Scaffold logging."""
        path = "aea-config.yaml"
        logging_config = self.generate(handlers)
        breakpoint()
        self.write(path, logging_config)
        return logging_config

    
    def options(self):
        """Get options for the logging scaffolder."""
        return list(HANDLERS.keys())
    
    def pre_script(self, path: str):
        """Pre script."""

        with open(path, "r") as file:
            yaml.safe_load(file)

    def post_script(self, path: str):
        """Post script."""
        pass


# we now add our cli command to the scaffold group
@scaffold.command()
@click.option("--handlers", "-h", multiple=True, default=[""], help="The handlers to scaffold.")
def logging(handlers):
    """Scaffold logging."""
    logging_scaffolder = LoggingScaffolder()
    logging_scaffolder.scaffold(handlers)
    logger.info("Logging scaffolded.")


import pytest

@pytest.fixture
def logging_scaffolder():
    """Logging scaffolder fixture."""
    return LoggingScaffolder()


def test_logging_scaffolder_options(logging_scaffolder):
    """test the logging scaffolder."""
    options = logging_scaffolder.options()
    assert options == ["console", "http"]


def test_logging_scaffolder_scaffold(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["console"])
    assert "console" in scaffold
    assert "http" not in scaffold


def test_logging_scaffolder_scaffold_all(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["all"])
    assert "console" in scaffold
    assert "http" in scaffold


def test_logging_scaffolder_scaffold_bad_handler(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["bad"])
    assert scaffold is None

"""
Implement scaffolding tooling
"""
from copy import deepcopy

import pytest
import rich_click as click
import yaml
from aea.cli.scaffold import scaffold

from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.utils import get_logger

logger = get_logger()

# we have a scaffold command group

BASE_LOGGING_CONFIG = yaml.safe_load(
    """
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
"""
)

CONSOLE_HANDLER = yaml.safe_load(
    """
console:
    class: rich.logging.RichHandler
    level: DEBUG
"""
)

HTTP_HANDLER = yaml.safe_load(
    """
http:
    class: logging.handlers.HTTPHandler
    formatter: standard
    level: INFO
    host: localhost:8000
    url: /log/
    method: POST
"""
)


HANDLERS = {
    "console": CONSOLE_HANDLER,
    "http": HTTP_HANDLER,
}


class Scaffolder:
    """Base scaffolder."""

    def write(self, path: str, content: str):
        """Write the content to the path."""
        with open(path, "w", encoding=DEFAULT_ENCODING) as file:
            file.write(content)


class LoggingScaffolder(Scaffolder):
    """Logging scaffolder."""

    def __init__(self):
        """Init scaffolder."""
        self.logger = get_logger()

    def generate(self, handlers: list):
        """Scaffold logging."""
        if not handlers:
            raise ValueError("No handlers provided")
        if handlers == ["all"]:
            handlers = HANDLERS

        else:
            for handler in handlers:
                if handler not in HANDLERS:
                    raise ValueError(f"Handler '{handler}' not found")
                handlers = {handler: HANDLERS[handler] for handler in handlers}
        logging_config = deepcopy(BASE_LOGGING_CONFIG)
        logging_config["logging_config"]["handlers"] = handlers
        logging_config["logging_config"]["loggers"]["aea"]["handlers"] = list(handlers.keys())
        return logging_config

    def scaffold(self, handlers: list):
        """Scaffold logging."""
        path = "aea-config.yaml"
        logging_config = self.generate(handlers)
        self.write(path, logging_config)
        return logging_config

    def options(self):
        """Get options for the logging scaffolder."""
        return list(HANDLERS.keys())


# we now add our cli command to the scaffold group
@scaffold.command()
@click.option("--handlers", "-h", multiple=True, default=[""], help="The handlers to scaffold.")
def logging(handlers):
    """Scaffold logging."""
    logging_scaffolder = LoggingScaffolder()
    logging_scaffolder.scaffold(handlers)
    logger.info("Logging scaffolded.")


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

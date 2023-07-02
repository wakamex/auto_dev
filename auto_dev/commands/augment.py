"""
Implement scaffolding tooling
"""
from copy import deepcopy
from pathlib import Path

import rich_click as click
import yaml

from auto_dev.base import build_cli
from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.utils import get_logger

logger = get_logger()

cli = build_cli(plugins=False)

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
class: rich.logging.RichHandler
level: INFO
"""
)

HTTP_HANDLER = yaml.safe_load(
    """
class: logging.handlers.HTTPHandler
formatter: standard
level: INFO
host: ${LOG_SERVER:str:localhost:8000}
url: /log/
method: POST
"""
)
LOGFILE_HANDLER = yaml.safe_load(
    """
class: logging.FileHandler
formatter: standard
filename: ${LOG_FILE:str:log.txt}
level: INFO
"""
)

HANDLERS = {
    "console": CONSOLE_HANDLER,
    "http": HTTP_HANDLER,
    "logfile": LOGFILE_HANDLER,
}


def write(path: str, content: dict):
    """Safe write the contents to the path using yaml."""
    with open(path, "w", encoding=DEFAULT_ENCODING) as file:
        yaml.dump(content, file, default_flow_style=False, sort_keys=False)


class LoggingScaffolder:
    """Logging scaffolder."""

    def __init__(self):
        """Init scaffolder."""
        self.logger = get_logger()

    def generate(self, handlers: list):
        """Scaffold logging."""
        self.logger.info(f"Generating logging config with handlers: {handlers}")
        if not handlers:
            raise ValueError("No handlers provided")
        if handlers == ["all"]:
            handlers = HANDLERS
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
        if not Path(path).exists():
            raise FileNotFoundError(f"File {path} not found")

        config = yaml.safe_load(Path(path).read_text(encoding=DEFAULT_ENCODING))
        if isinstance(config, dict):
            aea_config = config
        else:
            aea_config = list(config)[0]
        logging_config = self.generate(handlers)
        aea_config.update(logging_config)
        write(path, aea_config)
        return logging_config


@cli.group()
def augment():
    """Scaffold commands."""


@augment.command()
@click.argument("handlers", nargs=-1, type=click.Choice(HANDLERS.keys()), required=True)
def logging(handlers):
    """Augment an aeas logging configuration."""
    logger.info(f"Augmenting logging with handlers: {handlers}")
    logging_scaffolder = LoggingScaffolder()
    logging_scaffolder.scaffold(handlers)
    logger.info("Logging scaffolded.")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

"""Command."""

from pathlib import Path

import rich_click as click
from aea.configurations.base import PublicId, PackageType
from aea.configurations.constants import PACKAGES, SERVICES

from auto_dev.base import build_cli
from auto_dev.utils import get_logger, load_autonolas_yaml
from auto_dev.exceptions import UserInputError
from auto_dev.scaffolder import BasePackageScaffolder
from auto_dev.commands.run import AgentRunner


logger = get_logger()

cli = build_cli(plugins=False)


@cli.group()
def convert() -> None:
    """Commands to convert between an agent and a service or vice versa."""


class ConvertCliTool(BasePackageScaffolder):
    """Config for the agent servce convert cli."""

    package_type = "service"

    def __init__(self, agent_public_id: PublicId, service_public_id: PublicId):
        """Init the config."""
        self.agent_public_id = (
            PublicId.from_str(agent_public_id) if isinstance(agent_public_id, str) else agent_public_id
        )
        self.service_public_id = (
            PublicId.from_str(service_public_id) if isinstance(service_public_id, str) else service_public_id
        )
        self.agent_runner = AgentRunner(self.agent_public_id, verbose=True, force=True, logger=logger)

    def validate(self):
        """Validate function be called before the conversion."""
        if not self.agent_public_id:
            msg = "Agent public id is required."
            raise UserInputError(msg)
        if not self.service_public_id:
            msg = "Service public id is required."
            raise UserInputError(msg)
        if not self.agent_runner.agent_dir.exists():
            return UserInputError(f"Agent directory {self.agent_runner.agent_dir} does not exist.")
        return None

    def generate(self, force: bool = False, number_of_agents: int = 1):
        """Convert from agent to service."""
        self.validate()
        agent_config, *overrides = load_autonolas_yaml(
            package_type=PackageType.AGENT, directory=self.agent_runner.agent_dir
        )
        self.check_if_service_exists(force, number_of_agents)
        self.create_service(agent_config, overrides)
        return True

    def create_service(self, agent_config, overrides):
        """Create the service from a jinja template."""

    def check_if_service_exists(self, force: bool = False, number_of_agents: int = 1):
        """Check if the service exists."""
        number_of_agents = max(1, number_of_agents)
        code_path = Path(PACKAGES) / self.service_public_id.author / SERVICES / self.service_public_id.name
        if code_path.exists():
            if not force:
                msg = f"Service {self.service_public_id} already exists."
                raise UserInputError(msg)
            logger.warning(f"Service {self.service_public_id} already exists. Overwriting ...")
            code_path.rmdir()
        return True


@convert.command()
@click.argument("agent_public_id", type=PublicId.from_str)
@click.argument("service_public_id", type=PublicId.from_str)
@click.option(
    "--number_of_agents", type=int, default=1, required=False, help="Number of agents to be included in the service."
)
def agent_to_service(agent_public_id: PublicId, service_public_id: PublicId, number_of_agents: int = 1) -> None:
    """Convert an agent to a service.

    Args:
    ----
        AGENT_PUBLIC_ID: The public id of the agent.
        SERVICE_PUBLIC_ID: The public id of the service to be converted to.

    Example:
    -------
        adev convert AGENT_PUBLIC_ID SERVICE_PUBLIC_ID

    """
    logger.info(f"Converting agent {agent_public_id} to service {service_public_id}.")
    converter = ConvertCliTool(agent_public_id, service_public_id)
    converter.generate(number_of_agents=number_of_agents)
    logger.info("Conversion complete. Service is ready! 🚀")

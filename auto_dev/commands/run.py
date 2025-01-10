"""Command to run an agent."""

import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Any
import os

import rich_click as click

from auto_dev.base import build_cli
from auto_dev.cli_executor import CommandExecutor

cli = build_cli()

@dataclass
class AgentRunner:
    """Class to manage running an agent."""

    agent_name: str
    verbose: bool
    force: bool
    logger: Any

    def run(self) -> None:
        """Run the agent."""
        self.logger.info(f"Fetching agent {self.agent_name} from the local package registry...")
        self.check_tendermint()
        self.check_agent_exists()
        self.fetch_agent()
        self.setup_agent()
        self.execute_agent()

    def check_tendermint(self) -> None:
        """Check if Tendermint is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=tendermint", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            if "tendermint" not in result.stdout:
                raise RuntimeError("Tendermint is not running.")
        except (subprocess.CalledProcessError, RuntimeError) as e:
            self.logger.error("Tendermint is not running. Please install and run Tendermint using Docker.")
            self.logger.error("You can start Tendermint with the following command:")
            self.logger.error("docker run -d --name tendermint tendermint/tendermint")
            sys.exit(1)

    def check_agent_exists(self) -> None:
        """Check if the agent already exists."""
        agent_name = self.agent_name.split('/')[1]
        if Path(agent_name).exists() and not self.force:
            self.logger.error(f"Agent `{agent_name}` already exists. Use --force to overwrite.")
            sys.exit(1)

    def fetch_agent(self) -> None:
        """Fetch the agent."""
        agent_name = self.agent_name.split('/')[1]
        if Path(agent_name).exists():
            if self.force:
                self.logger.info(f"Removing existing agent `{agent_name}` due to --force option.")
                self.execute_command(f"rm -rf {agent_name}")
            else:
                self.logger.error(f"Agent `{agent_name}` already exists. Use --force to overwrite.")
                sys.exit(1)
        
        command = f"aea -s fetch {self.agent_name} --local"
        self.execute_command(command)

    def setup_agent(self) -> None:
        """Setup the agent."""
        agent_name = self.agent_name.split('/')[1]
        agent_author = self.agent_name.split('/')[0]

        self.logger.info(f"Agent author: {agent_author}")
        self.logger.info(f"Agent name: {agent_name}")

        Path(agent_name).mkdir(exist_ok=True)
        self.change_directory(agent_name)
        self.manage_keys()
        self.install_dependencies()
        self.issue_certificates()

    def manage_keys(self) -> None:
        """Manage Ethereum keys."""
        if not Path("../ethereum_private_key.txt").exists():
            self.execute_command("aea -s generate-key ethereum && aea -s add-key ethereum")
        else:
            self.execute_command("cp ../ethereum_private_key.txt ./ethereum_private_key.txt")
            self.execute_command("aea -s add-key ethereum")

    def install_dependencies(self) -> None:
        """Install agent dependencies."""
        self.execute_command("aea -s install")

    def issue_certificates(self) -> None:
        """Issue certificates for agent."""
        if not Path("../certs").exists():
            self.execute_command("aea -s issue-certificates")
        else:
            self.execute_command("cp -r ../certs ./")

    def execute_agent(self) -> None:
        """Execute the agent."""
        self.execute_command("aea -s run")

    def execute_command(self, command: str) -> None:
        """Execute a shell command."""
        cli_executor = CommandExecutor(command=command.split(" "))
        result = cli_executor.execute(stream=True, verbose=self.verbose)
        if not result:
            self.logger.error(f"Command failed: {command}")
            sys.exit(1)

    def change_directory(self, directory: str) -> None:
        """Change the current working directory."""
        os.chdir(directory)

@cli.command()
@click.argument("agent_name", type=str, required=True)
@click.option("-v", "--verbose", is_flag=True, help="Verbose mode.", default=False)
@click.option("--force", is_flag=True, help="Force overwrite of existing agent", default=False)
@click.pass_context
def run(ctx, agent_name: str, verbose: bool, force: bool) -> None:
    """Run an agent."""
    logger = ctx.obj["LOGGER"]
    logger.info(f"Running agent {agent_name}... 🚀")
    runner = AgentRunner(agent_name=agent_name, verbose=verbose, force=force, logger=logger)
    runner.run()
    logger.info("Agent run complete. 😎")

if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

"""This module contains the service logic for publishing agents."""

import shutil
from pathlib import Path

from aea.configurations.base import PublicId
from aea.configurations.data_types import PackageType

from auto_dev.enums import FileType
from auto_dev.utils import change_dir, load_autonolas_yaml
from auto_dev.exceptions import OperationError
from auto_dev.cli_executor import CommandExecutor


def ensure_local_registry(verbose: bool = False) -> None:
    """Ensure a local registry exists.

    Args:
        verbose: whether to show verbose output.

    Raises:
        OperationError: if the command fails.
    """
    if not Path("packages").exists():
        command = CommandExecutor(["poetry", "run", "autonomy", "packages", "init"])
        result = command.execute(verbose=verbose)
        if not result:
            msg = f"Command failed: {command.command}"
            raise OperationError(msg)


def publish_agent(public_id: PublicId, verbose: bool = False) -> None:
    """Publish an agent.

    Args:
        public_id: the public_id of the agent.
        verbose: whether to show verbose output.

    Raises:
        OperationError: if the command fails.
    """
    publish_commands = ["aea publish --push-missing --local"]
    with change_dir(public_id.name):
        # we have to do a horrible hack here, regards to the customs as they are not being published.
        # please see issue.
        agent_config_yaml = load_autonolas_yaml(PackageType.AGENT)
        for package in agent_config_yaml[0]["customs"]:
            custom_id = PublicId.from_str(package)
            # We need to copy the customs to the parent now.
            customs_path = Path("vendor") / custom_id.author / "customs" / custom_id.name
            package_path = Path("..") / "packages" / custom_id.author / "customs" / custom_id.name
            if not package_path.exists():
                shutil.copytree(
                    customs_path,
                    package_path,
                )

        for command in publish_commands:
            command = CommandExecutor(
                command.split(" "),
            )
            result = command.execute(verbose=verbose)
            if not result:
                msg = f"""
                Command failed: {command.command}
                Error: {command.stderr}
                stdout: {command.stdout}"""
                raise OperationError(msg)
        lock_packages(verbose)


def lock_packages(verbose: bool = False) -> None:
    """Lock the packages after publishing."""

    command = CommandExecutor(
        ["bash", "-c", "yes dev | autonomy packages lock"],
    )
    result = command.execute(verbose=verbose)
    if not result and command.return_code not in [0, 1]:
        msg = f"Packages lock failed with exit code {command.return_code}"
        raise OperationError(msg)

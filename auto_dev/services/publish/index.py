"""This module contains the service logic for publishing agents."""

import shutil
from typing import Optional
from pathlib import Path

from aea.configurations.base import PublicId
from aea.configurations.data_types import PackageType

from auto_dev.enums import FileType, LockType
from auto_dev.utils import change_dir, get_logger, load_autonolas_yaml
from auto_dev.exceptions import OperationError
from auto_dev.cli_executor import CommandExecutor


logger = get_logger()


class PublishService:
    """Service for publishing agents and managing packages."""

    def __init__(self, verbose: bool = False):
        """Initialize the publish service.

        Args:
            verbose: whether to show verbose output.
        """
        self.verbose = verbose

    def ensure_local_registry(self) -> None:
        """Ensure a local registry exists.

        Raises:
            OperationError: if the command fails.
        """
        # If we're in an agent directory, packages should be in parent dir
        packages_dir = Path("../packages") if Path("aea-config.yaml").exists() else Path("packages")
        if not packages_dir.exists():
            # Need to cd to parent dir if initializing there
            if packages_dir.parent != Path("."):
                with change_dir(".."):
                    command = CommandExecutor(["poetry", "run", "autonomy", "packages", "init"])
                    result = command.execute(verbose=self.verbose)
                    if not result:
                        msg = f"Command failed: {command.command}"
                        raise OperationError(msg)
            else:
                command = CommandExecutor(["poetry", "run", "autonomy", "packages", "init"])
                result = command.execute(verbose=self.verbose)
                if not result:
                    msg = f"Command failed: {command.command}"
                    raise OperationError(msg)

    def _get_package_path(self, custom_id: PublicId, package_type: str = "customs") -> Path:
        """Get the correct package path based on whether we're inside an agent directory.

        Args:
            custom_id: The custom package ID.
            package_type: The type of package ("customs" or "agents"). Defaults to "customs".

        Returns:
            The correct package path.
        """
        # If we're in an agent directory (aea-config.yaml exists), use relative path
        base = "../packages" if Path("aea-config.yaml").exists() else "packages"
        return Path(base) / custom_id.author / package_type / custom_id.name

    def _publish_agent_internal(self, force: bool = False) -> None:
        """Internal function to handle agent publishing logic.

        Args:
            force: If True, remove existing package before publishing.

        Raises:
            OperationError: if the command fails.
        """
        # Load config to get agent details
        agent_config_yaml = load_autonolas_yaml(PackageType.AGENT)
        agent_name = agent_config_yaml[0]["agent_name"]
        author = agent_config_yaml[0]["author"]

        # Check if package exists and handle force flag
        agent_id = PublicId(author, agent_name, "latest")
        package_path = self._get_package_path(agent_id, "agents")
        print(package_path)
        if package_path.exists():
            if force:
                logger.info(f"Removing existing package at {package_path}")
                shutil.rmtree(package_path)
            else:
                msg = f"Package already exists at {package_path}. Use --force to overwrite."
                raise OperationError(msg)

        publish_commands = ["aea publish --push-missing --local"]
        # we have to do a horrible hack here, regards to the customs as they are not being published.
        # please see issue.
        for package in agent_config_yaml[0]["customs"]:
            custom_id = PublicId.from_str(package)
            # We need to copy the customs to the parent now.
            customs_path = Path("vendor") / custom_id.author / "customs" / custom_id.name
            package_path = self._get_package_path(custom_id)
            if not package_path.exists():
                shutil.copytree(
                    customs_path,
                    package_path,
                )

        for command in publish_commands:
            command = CommandExecutor(
                command.split(" "),
            )
            result = command.execute(verbose=self.verbose)
            if not result:
                msg = f"""
                Command failed: {command.command}
                Error: {command.stderr}
                stdout: {command.stdout}"""
                raise OperationError(msg)

    def publish_agent(
        self,
        public_id: Optional[PublicId] = None,
        lock_type: Optional[LockType] = None,
        force: bool = False,
    ) -> None:
        """Publish an agent.

        Args:
            public_id: Optional. The public_id of the agent. If not provided,
                assumes we're already in the agent directory.
            lock_type: the type of lock to apply (dev or third_party). If provided, packages will be locked.
            force: If True, remove existing package before publishing.

        Raises:
            OperationError: if the command fails.
        """
        if public_id:
            logger.info(f"Publishing agent {public_id}")
            if Path(public_id.name).exists():
                with change_dir(public_id.name):
                    self._publish_agent_internal(force)
            else:
                raise OperationError(f"Agent directory {public_id.name} does not exist")
        else:
            logger.info("Publishing agent from current directory")
            # Verify we're in an agent directory by checking for aea-config.yaml
            if not Path("aea-config.yaml").exists():
                raise OperationError("Not in an agent directory (aea-config.yaml not found)")
            self._publish_agent_internal(force)

        logger.info("Agent published!")
        if lock_type is not None:
            self.lock_packages(lock_type)

    def lock_packages(self, lock_type: LockType = LockType.DEV) -> None:
        """Lock the packages after publishing.

        Args:
            lock_type: the type of lock to apply (dev or third_party).
        """

        logger.info(f"Locking packages as {lock_type.value}")

        command = CommandExecutor(
            ["bash", "-c", f"yes {lock_type.value} | autonomy packages lock"],
        )
        result = command.execute(verbose=self.verbose)
        if not result and command.return_code not in [0, 1]:
            msg = f"Packages lock failed with exit code {command.return_code}"
            raise OperationError(msg)
        logger.info("Packages locked")

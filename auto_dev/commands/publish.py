"""This module contains the logic for the publish command."""

from pathlib import Path

import rich_click as click
from aea.configurations.base import PublicId

from auto_dev.base import build_cli
from auto_dev.utils import change_dir
from auto_dev.constants import AGENT_PUBLISHED_SUCCESS_MSG
from auto_dev.exceptions import OperationError
from auto_dev.services.publish.index import PackageManager


cli = build_cli()


@cli.command()
@click.argument(
    "public_id",
    type=PublicId.from_str,
    required=False,
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite if package already exists",
    default=False,
)
@click.pass_context
def publish(ctx, public_id: str = None, force: bool = False) -> None:
    """
    Publish an agent to the local registry.

    Args:
        public_id: Optional. The public_id of the agent in the open-autonmy format i.e. `author/agent`.
                  If not provided, assumes you're inside the agent directory.
        force: If True, will overwrite existing package.

    Example usage:
        From parent directory: `adev publish author/agent`
        From agent directory: `adev publish`
        With force: `adev publish --force`
    """
    verbose = ctx.obj["VERBOSE"]
    logger = ctx.obj["LOGGER"]

    if public_id:
        logger.info(f"Publishing agent {public_id}")
    else:
        logger.info("Publishing agent from current directory")

    try:
        package_manager = PackageManager(verbose=verbose)

        # If we're given a public_id, we need to cd into that directory first
        if public_id:
            if isinstance(public_id, str):
                public_id = PublicId.from_str(public_id)

            agent_path = Path(public_id.name)
            if not agent_path.exists():
                # Try looking in the packages directory
                packages_path = Path("packages") / public_id.author / "agents" / public_id.name
                if not packages_path.exists():
                    raise OperationError(f"Agent directory not found at {agent_path} or {packages_path}")
                agent_path = packages_path

            with change_dir(agent_path):
                package_manager.publish_agent(force=force)
        else:
            # No public_id means we should already be in an agent directory
            if not Path("aea-config.yaml").exists():
                raise OperationError("Not in an agent directory (aea-config.yaml not found)")
            package_manager.publish_agent(force=force)

        click.secho(AGENT_PUBLISHED_SUCCESS_MSG, fg="green")
        logger.info("Agent published successfully.")

    except OperationError as e:
        click.secho(str(e), fg="red")
        ctx.exit(1)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

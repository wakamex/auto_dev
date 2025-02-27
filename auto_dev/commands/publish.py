"""This module contains the logic for the publish command."""

from pathlib import Path

import rich_click as click
from aea.configurations.base import PublicId

from auto_dev.base import build_cli
from auto_dev.utils import change_dir
from auto_dev.constants import AGENT_PUBLISHED_SUCCESS_MSG
from auto_dev.exceptions import OperationError
from auto_dev.commands.run import AgentRunner
from auto_dev.services.package_manager.index import PackageManager


cli = build_cli()


@cli.command()
@click.argument(
    "public_id",
    type=PublicId.from_str,
    required=True,
)
@click.option(
    "--force/--no-force",
    is_flag=True,
    help="Force overwrite if package already exists",
    default=False,
)
@click.pass_context
def publish(ctx, public_id: PublicId = None, force: bool = False) -> None:
    """
    Publish an agent to the local registry.

    Args:
        public_id: The public_id of the agent in the open-autonmy format i.e. `author/agent`.
                   If not provided, assumes you're inside the agent directory. This will be the
                   name of the package published.
        force: If True, will overwrite existing package.

    Example usage:
        From agent directory: `adev publish author/new_agent --force/--no-force`
        With force: `adev publish --force`
    """
    verbose = ctx.obj["VERBOSE"]
    logger = ctx.obj["LOGGER"]

    try:
        agent_runner = AgentRunner(
            agent_name=public_id,
            logger=logger,
            verbose=verbose,
            force=force,
        )
        if not agent_runner.is_in_agent_dir():
            raise OperationError(
                "Not in an agent directory (aea-config.yaml not found) Please enter the agent directory to publish"
            )
        package_manager = PackageManager(verbose=verbose)
        package_manager.publish_agent(force=force, new_public_id=public_id)
        click.secho(AGENT_PUBLISHED_SUCCESS_MSG, fg="green")
        logger.info("Agent published successfully.")
    except OperationError as e:
        click.secho(str(e), fg="red")
        ctx.exit(1)
    except Exception as e:
        logger.error(str(e))
        logger.error("Agent publish failed. Please consider running with --verbose flag for more information.")
        ctx.exit(1)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

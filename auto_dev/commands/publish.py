"""This module contains the logic for the publish command."""

import rich_click as click
from aea.configurations.base import PublicId

from auto_dev.base import build_cli
from auto_dev.exceptions import OperationError
from auto_dev.services.publish.index import publish_agent, ensure_local_registry


AGENT_PUBLISHED_SUCCESS_MSG = "Agent published successfully."

cli = build_cli()


@cli.command()
@click.argument(
    "public_id",
    type=PublicId.from_str,
)
@click.pass_context
def publish(ctx, public_id: str) -> None:
    """
    Publish an agent to the local registry.

    Args:
        public_id: the public_id of the agent in the open-autonmy format i.e. `author/agent`

    Example usage:
        `adev publish author/agent`
    """
    verbose = ctx.obj["VERBOSE"]
    logger = ctx.obj["LOGGER"]
    logger.info(f"Publishing agent {public_id}")

    try:
        ensure_local_registry(verbose)
        publish_agent(public_id, verbose)
        click.secho(AGENT_PUBLISHED_SUCCESS_MSG, fg="green")
        logger.info(f"Agent {public_id} published successfully.")
    except OperationError as e:
        click.secho(str(e), fg="red")
        raise click.Abort() from e


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

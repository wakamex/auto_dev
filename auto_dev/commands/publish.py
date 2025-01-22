"""This module contains the logic for the publish command."""

import rich_click as click
from aea.configurations.base import PublicId

from auto_dev.base import build_cli
from auto_dev.enums import LockType
from auto_dev.exceptions import OperationError
from auto_dev.services.publish.index import PublishService
from auto_dev.constants import AGENT_PUBLISHED_SUCCESS_MSG




cli = build_cli()


@cli.command()
@click.argument(
    "public_id",
    type=PublicId.from_str,
    required=False,
)
@click.option(
    "--lock-type",
    type=click.Choice([t.value for t in LockType], case_sensitive=False),
    help="The type of lock to apply (dev or third_party). If not provided, defaults to none",
    default=None,
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite if package already exists",
    default=False,
)
@click.pass_context
def publish(ctx, public_id: str = None, lock_type: str = None, force: bool = False) -> None:
    """
    Publish an agent to the local registry.

    Args:
        public_id: Optional. The public_id of the agent in the open-autonmy format i.e. `author/agent`.
                  If not provided, assumes you're inside the agent directory.
        lock_type: Optional. The type of lock to apply (dev or third_party). If not provided, defaults to none.
        force: If True, will overwrite existing package.

    Example usage:
        From parent directory: `adev publish author/agent`
        From agent directory: `adev publish`
        With force: `adev publish --force`
        With lock: `adev publish --lock-type dev`
    """
    verbose = ctx.obj["VERBOSE"]
    logger = ctx.obj["LOGGER"]

    if public_id:
        logger.info(f"Publishing agent {public_id}")
    else:
        logger.info("Publishing agent from current directory")

    try:
        publish_service = PublishService(verbose=verbose)
        publish_service.ensure_local_registry()

        if public_id:
            try:
                public_id = PublicId.from_str(public_id)
            except ValueError as e:
                raise click.ClickException(f"Invalid value for '[PUBLIC_ID]': {public_id}") from e

        publish_service.publish_agent(public_id, lock_type=LockType(lock_type) if lock_type else None, force=force)
        click.secho(AGENT_PUBLISHED_SUCCESS_MSG, fg="green")
        logger.info("Agent published successfully.")
    except OperationError as e:
        click.secho(str(e), fg="red")
        raise click.Abort() from e


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

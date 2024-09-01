"""This module contains the logic for the fmt command."""

import os
from pathlib import Path

import rich_click as click

from auto_dev.fmt import multi_thread_fmt, single_thread_fmt
from auto_dev.base import build_cli
from auto_dev.utils import get_packages, isolated_filesystem
from auto_dev.constants import AUTO_DEV_FOLDER, AUTONOMY_PACKAGES_FILE
from auto_dev.cli_executor import CommandExecutor


cli = build_cli()


def get_available_agents() -> list[str]:
    """Get the available agents."""
    packages = get_packages(Path(AUTO_DEV_FOLDER) / AUTONOMY_PACKAGES_FILE, "third_party", check=False, hashmap=True)
    return {f"{str(agent.parent.parent.stem)}/{str(agent.stem)}": ipfs_hash for agent, ipfs_hash in packages.items()}


available_agents = get_available_agents()


@cli.command()
@click.argument("name", type=str)
@click.option("-t", "--template", type=click.Choice(available_agents), required=True)
@click.option("-f", "--force", is_flag=True, help="Force the operation.")
@click.option("-p", "--publish", is_flag=True, help="Force the operation.", default=False)
@click.pass_context
def create(ctx, name: str, template: str, force: bool, publish: bool) -> None:
    f"""
    Create a new agent from a template.
    :param name: the name of the agent.
    :param template: the template to use.
    """

    is_proposed_path_exists = Path(name).exists()
    if is_proposed_path_exists and not force:
        click.secho(
            f"Directory {name} already exists. Please remove it or use the --force flag to overwrite it.",
            fg="red",
        )
        return
    if is_proposed_path_exists and force:
        click.secho(
            f"Directory {name} already exists. Removing it.",
            fg="yellow",
        )
        command = CommandExecutor(
            [
                "rm",
                "-rf",
                name,
            ]
        )
        result = command.execute(verbose=ctx.obj["VERBOSE"])
        if not result:
            click.secho(f"Command failed: {command.command}", fg="red")
            return
        click.secho("Command executed successfully.", fg="green")

    verbose = ctx.obj["VERBOSE"]
    logger = ctx.obj["LOGGER"]
    logger.info(f"Creating agent {name} from template {template}")

    ipfs_hash = available_agents[template]

    create_commands = [
        f"poetry run autonomy fetch {ipfs_hash} --alias {name}",
    ]

    for command in create_commands:
        command = CommandExecutor(
            command.split(" "),
        )
        result = command.execute(verbose=verbose)
        if not result:
            click.secho(f"Command failed: {command.command}", fg="red")
            click.secho(f"Failed to create agent {name}.", fg="red")
            return
        click.secho("Command executed successfully.", fg="yellow")

    if publish:
        os.chdir(name)
        publish_commands = [
            "aea publish --push-missing --local",
        ]

        for command in publish_commands:
            command = CommandExecutor(
                command.split(" "),
            )
            result = command.execute(verbose=verbose)
            if not result:
                click.secho(f"Command failed: {command.command}", fg="red")
                click.secho(f"Error: {command.stderr}", fg="red")
                click.secho(f"stdout: {command.stdout}", fg="red")
                return
            click.secho("Command executed successfully.", fg="yellow")

        # We now clean up the agent
        os.chdir("..")
        command = CommandExecutor(
            [
                "rm",
                "-rf",
                name,
            ]
        )
        result = command.execute(verbose=verbose)
        if not result:
            click.secho(f"Command failed: {command.command}", fg="red")
            return
        click.secho(f"Agent {name} published successfully.", fg="green")
    click.secho(f"Agent {name} created successfully.", fg="green")

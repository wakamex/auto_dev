"""

reads in 2 github repos.

One is the parent repo, the other is the child repo.

The child repo is dependent on the parent repo.

When there is a change in the parent repo, we want to update the child repo.

The dependencies are depfined in a file called packages/packages.json

this is structures as follows:

{
    "dev": {
        "aea_dep1": "ipfshash",
        "aea_dep2": "ipfshash",
        },
    "third_party": {
        "aea_dep3": "ipfshash",
        "aea_dep4": "ipfshash",
        },
}   

The ipfshash is the hash of the package.

We want to be able to update the hash of the package.       

"""
import json
import logging
import shutil
from pathlib import Path
from typing import Dict

import rich_click as click
import yaml

from auto_dev.base import build_cli
from auto_dev.constants import DEFAULT_ENCODING

PARENT = Path("repo_1")
CHILD = Path("repo_2")


def get_package_json(repo: Path) -> Dict[str, Dict[str, str]]:
    """
    We get the package json.
    """
    package_json = repo / "packages" / "packages.json"
    with open(package_json, encoding=DEFAULT_ENCODING) as file_pointer:
        package_dict = yaml.safe_load(file_pointer)
    return package_dict


def write_package_json(repo: Path, package_dict: Dict[str, Dict[str, str]]) -> None:
    """
    We write the package json.
    """
    package_json = repo / "packages" / "packages.json"
    with open(package_json, "w", encoding=DEFAULT_ENCODING) as file_pointer:
        json.dump(package_dict, file_pointer, indent=4)


def get_package_hashes(repo: Path) -> Dict[str, str]:
    """
    We get the package hashes.
    """
    package_dict = get_package_json(repo)
    package_hashes = {}
    for _, package_type_dict in package_dict.items():
        for package_name, package_hash in package_type_dict.items():
            package_hashes[package_name] = package_hash
    return package_hashes


def get_proposed_dependency_updates(parent_repo: Path, child_repo: Path) -> Dict[str, str]:
    """
    We get the proposed dependency updates.
    """
    parent_package_hashes = get_package_hashes(parent_repo)
    child_package_hashes = get_package_hashes(child_repo)
    proposed_dependency_updates = {}
    for package_name, package_hash in parent_package_hashes.items():
        if package_name in child_package_hashes:
            if package_hash != child_package_hashes[package_name]:
                proposed_dependency_updates[package_name] = package_hash
    return proposed_dependency_updates


def update_package_json(repo: Path, proposed_dependency_updates: Dict[str, str]) -> None:
    """
    We update the package json.
    """
    package_dict = get_package_json(repo)
    for package_type, package_type_dict in package_dict.items():
        for package_name, _ in package_type_dict.items():
            if package_name in proposed_dependency_updates:
                package_dict[package_type][package_name] = proposed_dependency_updates[package_name]
    write_package_json(repo, package_dict)


def from_key_to_path(key: str) -> Path:
    """
    We get the path from the key string some examples of the keys are;
    agent/eightballer/custom_balance_poller/0.1.0
    where the folder to be removed is;
    packages/eightballer/agents/custom_balance_poller
    """
    parts = key.split("/")

    path_list = [
        "packages",
        parts[1],
        parts[0] + "s",
        parts[2],
    ]
    return Path(*path_list)


def remove_old_package(repo: Path, proposed_dependency_updates: Dict[str, str]) -> None:
    """
    We remove the old package directories.
    """
    for package_name, _ in proposed_dependency_updates.items():
        path = from_key_to_path(package_name)
        path = repo / path
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def main(
    parent_repo: Path,
    child_repo: Path,
    logger: logging.Logger,
    auto_confirm: bool = False,
) -> None:
    """
    We run the main function.
    """
    proposed = get_proposed_dependency_updates(parent_repo=parent_repo, child_repo=child_repo)
    if not proposed:
        logger.info("No changes required. 😎")
        return
    for package_name, package_hash in proposed.items():
        logger.info(f"Updating {package_name} to {package_hash}")
    if not auto_confirm:
        click.confirm("Do you want to update the package?", abort=True)
    logger.info("Updating the packages json... 📝")
    update_package_json(repo=child_repo, proposed_dependency_updates=proposed)
    logger.info("Removing the old packages directories... 🗑")
    remove_old_package(repo=child_repo, proposed_dependency_updates=proposed)
    logger.info("Done. 😎")


cli = build_cli()


@cli.command()
@click.option(
    "-p",
    "--parent-repo",
    default=PARENT,
    help="The parent repo.",
    type=Path,
    required=True,
)
@click.option(
    "-c",
    "--child-repo",
    help="The child repo.",
    type=Path,
    required=True,
)
@click.option(
    "--auto-confirm",
    default=False,
    help="Auto confirm the changes.",
)
@click.pass_context
def deps(
    ctx: click.Context,
    parent_repo: Path,
    child_repo: Path,
    auto_confirm: bool = False,
) -> None:
    """
    We update the dependencies.
    """
    logger = ctx.obj["LOGGER"]
    logger.info("Updating the dependencies... 📝")
    main(parent_repo=parent_repo, child_repo=child_repo, auto_confirm=auto_confirm, logger=logger)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

"""
We release the package.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rich_click as click
import toml

from auto_dev.base import build_cli
from auto_dev.cli_executor import CommandExecutor
from auto_dev.constants import DEFAULT_ENCODING


@dataclass
class Releaser:
    """
    class to mamange the versions
    """

    logger: Any
    dep_path: str = "pyproject.toml"
    verbose: bool = True

    def current_version(self):
        """
        We get the current version.
        """
        with open(self.dep_path, "r", encoding=DEFAULT_ENCODING) as file_pointer:
            data = toml.load(file_pointer)
        return data["tool"]["poetry"]["version"]

    def get_new_version(self):
        """
        We get the new version by incrementing the current version.
        if we are at v0.1.0 we will get v0.1.1
        current version is in the format v0.1.0
        """
        current_version = self.current_version()
        parts = current_version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)

    def update_version(self, new_version):
        """
        We update the version.
        """
        with open(self.dep_path, "r", encoding=DEFAULT_ENCODING) as file_pointer:
            data = toml.load(file_pointer)
        data["tool"]["poetry"]["version"] = new_version
        with open(self.dep_path, "w", encoding=DEFAULT_ENCODING) as file_pointer:
            toml.dump(data, file_pointer)

    def post_release(self):
        """
        We run the post release.
        """

    def release(self):
        """
        We run the release.
        """
        self.logger.info("Running the release... 🚀")
        self.logger.info(f"Current version is {self.current_version()}. 🚀")
        self.logger.info(f"New version will be {self.get_new_version()}. 🚀")
        if not self.pre_release():
            self.logger.error("Pre release failed. 😭")
            return False
        new_version = self.get_new_version()
        if not self.update_version(new_version):
            self.logger.error("Update version failed. 😭")
            return False
        if not self.post_release():
            self.logger.error("Post release failed. 😭")
            return False
        self.logger.info(f"New version is {new_version} 🎉")
        return True

    def pre_release(self):
        """
        We run the pre release.
        """
        # we checkout to a new branch for the release
        new_version = self.get_new_version()
        cli_tool = CommandExecutor(
            command=f"git checkout -b v{new_version}".split(" "),
        )
        return cli_tool.execute(verbose=self.verbose, stream=self.verbose)


cli = build_cli()


@cli.command()
@click.option(
    "-p",
    "--dep-path",
    default="pyproject.toml",
    help="The dependency path.",
    type=Path,
    required=True,
)
@click.option(
    "--verbose",
    default=False,
    help="Verbose mode.",
)
@click.pass_context
def release(
    ctx: click.Context,
    dep_path: Path,
    verbose: bool = False,
) -> None:
    """
    We release the package.
    """
    logger = ctx.obj["LOGGER"]
    logger.info("Releasing the package... 🚀")
    releaser = Releaser(dep_path=dep_path, verbose=verbose, logger=logger)
    if not releaser.release():
        logger.error("Release failed. 😭")
        raise click.Abort()
    logger.info("Done. 😎")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

"""
Module to assist with repo setup and management.
contains the following commands;
    - scaffold
        - all
        - .gitignore
        . .githubworkflows
        . .README.md
        . pyproject.toml

"""
from dataclasses import dataclass

# we will use a class based approach to scaffold the repos, so we can use it in multiple places
from pathlib import Path
from typing import List

import rich_click as click

from auto_dev.base import build_cli
from auto_dev.constants import DEFAULT_ENCODING

cli = build_cli()

PYTHON_GIT_IGNORE = """
__pycache__/
"""
OPEN_AUTONOMY_GIT_IGNORE = (
    PYTHON_GIT_IGNORE
    + """
keys.json
**/*_private_key.txt
"""
)


@dataclass
class ScaffoldFile:
    """Class to store a file to scaffold."""

    name: str
    content: str


@dataclass
class RepoType:
    """Class to store a repo type."""

    name: str
    files: List[ScaffoldFile]


class RepoScaffolder:
    """Class to scaffold a new repo."""

    def __init__(self, verbose, logger):
        self.verbose = verbose
        self.logger = logger

    def scaffold(self, type_of_repo, files: List[str]):
        """Scaffold files for a new repo."""
        if type_of_repo not in SUPPORTED_REPO_TYPES:
            raise ValueError(
                f"Repo type not supported: {type_of_repo}" + f"Repo types must be one of: {SUPPORTED_REPO_TYPES.keys()}"
            )
        repo_type = SUPPORTED_REPO_TYPES[type_of_repo]
        for filen in files:
            if filen not in repo_type.files:
                raise ValueError(f"File not supported: {filen}" + f"Files must be one of: {repo_type.files}")
            self.check_and_write_file(filen, "")

    def check_and_write_file(self, path, content):
        """Check if a file exists and write it if it doesn't."""
        path = Path(path)
        if path.exists():
            raise FileExistsError(f"File already exists: {path}")
        if self.verbose:
            self.logger.info(f"Writing file: {path}")
        path.write_text(content, encoding=DEFAULT_ENCODING)


PYTHON_REPO_TYPE = RepoType(
    name="python",
    files=[
        ScaffoldFile(name=".gitignore", content=PYTHON_GIT_IGNORE),
        ScaffoldFile(name="README.md", content=""),
        ScaffoldFile(name="pyproject.toml", content=""),
        ScaffoldFile(name=".github/workflows/ci.yml", content=""),
    ],
)

OPEN_AUTONOMY_REPO_TYPE = RepoType(
    name="open-autonomy",
    files=[
        ScaffoldFile(name=".gitignore", content=OPEN_AUTONOMY_GIT_IGNORE),
    ],
)


SUPPORTED_REPO_TYPES = {
    PYTHON_REPO_TYPE.name: PYTHON_REPO_TYPE,
}


@cli.group()
def repo():
    """Scaffold commands."""


@repo.command()
@click.option(
    "-t",
    "--type-of-repo",
    help="Type of repo to scaffold",
    type=click.Choice(SUPPORTED_REPO_TYPES.keys()),
    required=True,
)
@click.option("--files", help="Files to scaffold", multiple=True, default=None)
@click.pass_context
def scaffold(ctx, type_of_repo, files):
    """Scaffold necessary files for a new repo."""
    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]
    logger.info(f"Scaffolding a new {type_of_repo} repo.")
    repo_type = SUPPORTED_REPO_TYPES[type_of_repo]
    if files == ():
        raise ValueError("No files provided." + f"Files must be one of: {[f.name for f in repo_type.files]}")
    scaffolder = RepoScaffolder(verbose, logger)
    scaffolder.scaffold(type_of_repo=type_of_repo, files=files)
    logger.info("Done.")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

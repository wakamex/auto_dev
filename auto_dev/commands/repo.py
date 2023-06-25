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
import importlib
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Dict, List

import rich_click as click

from auto_dev.base import build_cli
from auto_dev.constants import DEFAULT_ENCODING, TEMPLATE_FOLDER

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

    content: str
    path: Path = None

    @property
    def name(self):
        """Get the name of the file."""
        return Path(self.path).stem + Path(self.path).suffix


@dataclass
class RepoType:
    """Class to store a repo type."""

    name: str
    files: Dict[str, ScaffoldFile]


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
                raise ValueError(
                    f"Files must be one of: `{list(repo_type.files.keys())}`. Howerver, `{filen}` was given."
                )
            new_file_generator = repo_type.files[filen]
            new_file_name = new_file_generator.name
            new_file_content = new_file_generator.content
            self.check_and_write_file(new_file_name, new_file_content)

    def check_and_write_file(self, path, content):
        """Check if a file exists and write it if it doesn't."""
        path = Path(path)
        if path.exists():
            raise FileExistsError(f"File already exists: {path}")
        if self.verbose:
            self.logger.info(f"Writing file: {path}")
        path.write_text(content, encoding=DEFAULT_ENCODING)


def test_get_supported_repo_types():
    """Test the get_supported_repo_types function."""
    assert get_supported_repo_types({}) == SUPPORTED_REPO_TYPES


def get_supported_repo_types(render_args) -> dict:
    """
    Get the supported repo types from the templates folder.
    We will do this by reading in from the libraries folders;
    """
    del render_args

    supported_repos = {}

    for template_folder in Path(TEMPLATE_FOLDER).glob("*"):
        files = glob(str(template_folder / "**/*"), recursive=True)
        scaffold_files = {}
        for filep in files:
            # our files are as .py files so we will need to import them
            # TypeError: the 'package' argument is required to perform a relative import
            # we will need to import the file and then call the render function
            if not filep.endswith(".py"):
                # we need to remove the .py from the end of the file
                continue

            template_path = Path(filep)
            import_path = f"auto_dev.data.repo.templates.{template_path.parent.name}.{template_path.stem}"
            template = importlib.import_module(import_path)
            file_output = template.TEMPLATE
            output_path = Path(template_path.stem + template.EXTENSION)
            scaffold_file = ScaffoldFile(path=output_path.name, content=file_output)
            scaffold_files[template_path.stem] = scaffold_file
        supported_repos[template_folder.name] = RepoType(name=template_folder, files=scaffold_files)
    return supported_repos


render_args = {
    "project_name": "test",
    "author": "8ball030",
    "email": "8ball030@gmail.com",
    "description": "test",
    "version": "0.1.0",
}

SUPPORTED_REPO_TYPES = get_supported_repo_types(render_args)


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
    if not Path(".git").exists():
        raise ValueError("Not in the top level of a git repo.")
    repo_type = SUPPORTED_REPO_TYPES[type_of_repo]
    if files == ():
        raise ValueError(f"No files provided. Must be one of: {list(repo_type.files.keys())}")
    scaffolder = RepoScaffolder(verbose, logger)
    scaffolder.scaffold(type_of_repo=type_of_repo, files=files)
    logger.info("Done.")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

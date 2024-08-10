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

import sys
from pathlib import Path
from shutil import rmtree

import rich_click as click
from aea.cli.utils.config import get_default_author_from_cli_config
from rich.progress import track
from rich.prompt import Prompt

from auto_dev.base import build_cli
from auto_dev.cli_executor import CommandExecutor
from auto_dev.constants import DEFAULT_ENCODING, SAMPLE_PYTHON_CLI_FILE, SAMPLE_PYTHON_MAIN_FILE, TEMPLATE_FOLDER
from auto_dev.enums import UserInput
from auto_dev.utils import change_dir

AGENT_PREFIX = "AutoDev: ->: {msg}"


def execute_commands(*commands: str, verbose: bool, logger, shell: bool = False) -> None:
    """Execute commands."""
    for command in commands:
        cli_executor = CommandExecutor(command=command.split(" "))
        result = cli_executor.execute(stream=False, verbose=verbose, shell=shell)
        if not result:
            logger.error(f"Command failed: {command}")
            logger.error(f"{cli_executor.stdout}")
            logger.error(f"{cli_executor.stderr}")
            sys.exit(1)


cli = build_cli()

render_args = {
    "project_name": "test",
    "author": get_default_author_from_cli_config(),
    "email": "8ball030@gmail.com",
    "description": "",
    "version": "0.1.0",
}

TEMPLATES = {f.name: f for f in Path(TEMPLATE_FOLDER).glob("*")}


class RepoScaffolder:
    """Class to scaffold a new repo."""

    def __init__(self, type_of_repo, logger, verbose):
        self.type_of_repo = type_of_repo
        self.logger = logger
        self.verbose = verbose
        self.scaffold_kwargs = render_args

    def scaffold(self):
        """Scaffold files for a new repo."""

        new_repo_dir = Path.cwd()
        template_folder = TEMPLATES[self.type_of_repo]
        all_found_files_recursive = list(template_folder.rglob("*"))
        paths = [f for f in all_found_files_recursive if f.is_file() or f.is_dir()]
        paths = sorted(paths, key=lambda x: x.is_dir())
        for file in track(paths, description=f"Scaffolding {self.type_of_repo} repo", total=len(paths)):
            self.logger.debug(f"Scaffolding `{str(file)}`")
            if file.is_dir():
                rel_path = file.relative_to(template_folder)
                target_file_path = new_repo_dir / rel_path
                target_file_path.mkdir(parents=True, exist_ok=True)
                continue
            rel_path = file.relative_to(template_folder)
            content = file.read_text(encoding=DEFAULT_ENCODING)
            if file.suffix == ".template":
                content = content.format(**self.scaffold_kwargs)
                target_file_path = new_repo_dir / rel_path.with_suffix("")
            else:
                target_file_path = new_repo_dir / rel_path
            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            target_file_path.write_text(content)


@cli.command()
@click.option(
    "-t",
    "--type-of-repo",
    help="Type of repo to scaffold",
    type=click.Choice(TEMPLATES),
    required=True,
)
@click.option("-f", "--force", is_flag=True, help="Force overwrite of existing repo", default=False)
@click.option("--auto-approve", is_flag=True, help="Automatically approve all prompts", default=False)
@click.argument("name", type=str, required=True)
@click.pass_context
def repo(ctx, name, type_of_repo, force, auto_approve):
    """Create a new repo and scaffold necessary files."""

    logger = ctx.obj["LOGGER"]
    verbose = ctx.obj["VERBOSE"]
    logger.info(f"Creating a new {type_of_repo} repo.")
    render_args["project_name"] = name
    if Path(name).exists() and not force:
        logger.error(f"Repo `{name}` already exists.\n\tPlease choose a different name or use the --force flag.")
        sys.exit(1)
    if Path(name).exists() and force:
        if not auto_approve:
            warning_msg = f"Overwrite existing repo `{name}`? This will delete all existing files. 💀 "
            confirm = Prompt.ask(
                AGENT_PREFIX.format(msg=warning_msg), choices=[UserInput.YES.value, UserInput.NO.value]
            )
            if UserInput(confirm) is UserInput.NO:
                logger.info("Exiting. No changes made.")
                sys.exit(1)
        logger.info(f"Overwriting existing repo `{name}`.")
        rmtree(name)
    Path(name).mkdir(exist_ok=False, parents=True)
    with change_dir(name):
        execute_commands("git init", "git checkout -b main", verbose=verbose, logger=logger)
        assert (Path.cwd() / ".git").exists()

        scaffolder = RepoScaffolder(type_of_repo, logger, verbose)
        scaffolder.scaffold()
        if type_of_repo == "autonomy":
            logger.info("Installing host deps. This may take a while!")
            execute_commands(
                "bash ./install.sh",
                verbose=verbose,
                logger=logger,
            )
            logger.info("Initialising autonomy packages.")
            execute_commands("autonomy packages init", verbose=verbose, logger=logger)
        elif type_of_repo == "python":
            src_dir = Path(name)
            src_dir.mkdir(exist_ok=False)
            logger.debug(f"Scaffolding `{str(src_dir)}`")
            (src_dir / "__init__.py").touch()
            (src_dir / "main.py").write_text(SAMPLE_PYTHON_MAIN_FILE)
            (src_dir / "cli.py").write_text(SAMPLE_PYTHON_CLI_FILE.format(project_name=name))
        else:
            raise NotImplementedError(f"Unsupported repo type: {type_of_repo}")
        logger.info(f"{type_of_repo.capitalize()} successfully setup.")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

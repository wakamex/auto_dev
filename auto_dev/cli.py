"""
Simple cli to allow users to perform the following actions against an autonomy repo;

- lint
- test
- build
"""

import rich_click as click
from rich.progress import track

from auto_dev.test import test_path

from .lint import check_path
from .utils import get_logger, get_packages
from .scaffolder import scaffold

click.rich_click.USE_RICH_MARKUP = True
# so we can pretty print the output

logger = get_logger()


@click.group()
# set debug to true to enable debug logging
@click.option("--debug/--no-debug", default=False)
def cli(debug=False):
    """Main auto dev command group."""
    if debug:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")





@cli.command()
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option(
    "-p",
    "--path",
    help="Path to code to lint. If not provided will lint all packages.",
    type=click.Path(exists=True, file_okay=False),
    default=None,
)
def lint(verbose, path):
    """
    Runs the linting tooling
    """
    logger.info("Linting Open Autonomy Packages")
    try:
        packages = get_packages() if not path else [path]
    except Exception as error:
        raise click.ClickException(f"Unable to get packages are you in the right directory? {error}")

    results = {}
    for package in track(range(len(packages)), description="Linting..."):
        logger.debug("Processing package: './%s'", packages[package])
        result = check_path(str(packages[package]), verbose=verbose)
        results[packages[package]] = result

    for package, result in results.items():
        if not result:
            logger.error("Package '%s' failed linting", package)

    if False in results.values():
        raise click.ClickException("Linting failed!")

    logger.info("Linting completed successfully!")


@cli.command()
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option(
    "-p",
    "--path",
    help="Path to directory to test. If not provided will test all packages.",
    type=click.Path(exists=True, file_okay=False),
    default=None,
)
def test(verbose, path):
    """
    Runs the test tooling
    """
    click.echo("Testing Open Autonomy Packages")
    try:
        packages = get_packages() if not path else [path]
    except Exception as error:
        raise click.ClickException(f"Unable to get packages are you in the right directory? {error}")
    results = {}
    for package in track(range(len(packages)), description="Testing..."):
        logger.debug("Processing package: './%s'", packages[package])
        result = test_path(str(packages[package]), verbose=verbose)
        results[packages[package]] = result

    for package in results.items():
        if not package:
            logger.error("Package '%s' failed testing", package)
    # if any of the results are false, we need to raise an exception
    if False in results.values():
        raise click.ClickException("Testing failed!")

    click.echo("Testing completed successfully!")

#
# @cli.command()
# def build():
#     """
#     Runs the build tooling
#     """
#     click.echo("Building...")
#     click.echo("Building complete!")
#
#
# @cli.command()
# def scaffold():
#     """
#     Runs the scaffolder tooling
#     """
#     click.echo("Scaffolding...")
#     scaffold()
#     click.echo("Scaffolding complete!")
#
# if __name__ == "__main__":
#
#     cli()
import os

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')

class MyCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and filename != '__init__.py':
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']


@click.command(cls=MyCLI)
def cli():
    pass

if __name__ == '__main__':
    cli()

"""
Test command cli module.
"""
import rich_click as click
from rich.progress import track

from auto_dev.test import test_path
from auto_dev.utils import get_packages


@click.group()
def cli():
    """Cli testing tooling."""


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
        result = test_path(str(packages[package]), verbose=verbose)
        results[packages[package]] = result

    for package in results.items():
        if not package:
            raise click.ClickException(f"Package: {package} failed testing")
    # if any of the results are false, we need to raise an exception
    if False in results.values():
        raise click.ClickException("Testing failed!")

    click.echo("Testing completed successfully!")

"""
This module contains the logic for the fmt command.
"""

from multiprocessing import Pool

import rich_click as click
from rich.progress import track

from auto_dev.base import build_cli
from auto_dev.fmt import Formatter
from auto_dev.utils import get_paths


def single_thread_fmt(paths, verbose, logger, remote=False):
    """Run the formatting in a single thread."""
    results = {}
    formatter = Formatter(verbose, remote=remote)
    local_formatter = Formatter(verbose, remote=False)
    for package in track(range(len(paths)), description="Formatting..."):
        path = paths[package]
        if verbose:
            logger.info(f"Formatting: {path}")
        result = formatter.format(path)
        if not result:
            result = local_formatter.format(path)
        results[package] = result
    return results


def multi_thread_fmt(paths, verbose, num_processes, remote=False):
    """Run the formatting in multiple threads."""
    formatter = Formatter(verbose, remote=remote)
    with Pool(num_processes) as pool:
        results = pool.map(formatter.format, paths)

    # We chekc with the local formatter if the remote formatter fails
    local_formatter = Formatter(verbose, remote=False)
    for i, result in enumerate(results):
        if not result:
            results[i] = local_formatter.format(paths[i])

    return dict(zip(paths, results))


cli = build_cli()


@cli.command()
@click.option(
    "-p",
    "--path",
    help="Path to code to format. If not provided will format all packages.",
    type=click.Path(exists=True, file_okay=False),
    default=None,
)
@click.option(
    "-co",
    "--changed-only",
    help="Only lint the files that have changed.",
    is_flag=True,
    default=False,
)
@click.pass_context
def fmt(ctx, path, changed_only):
    """
    Runs the formatting tooling
    """
    verbose = ctx.obj["VERBOSE"]
    num_processes = ctx.obj["NUM_PROCESSES"]
    logger = ctx.obj["LOGGER"]
    remote = ctx.obj["REMOTE"]
    logger.info("Formatting Open Autonomy Packages...")
    logger.info(f"Remote: {remote}")
    paths = get_paths(path, changed_only)
    logger.info(f"Formatting {len(paths)} files...")
    if num_processes > 1:
        results = multi_thread_fmt(paths, verbose, num_processes, remote)
    else:
        results = single_thread_fmt(paths, verbose, logger, remote)
    passed = sum(results.values())
    failed = len(results) - passed
    logger.info(f"Formatting completed with {passed} passed and {failed} failed")
    if failed > 0:
        raise click.ClickException("Formatting failed!")

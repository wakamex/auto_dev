"""Module for testing the project."""

from multiprocessing import cpu_count

from auto_dev.cli_executor import CommandExecutor


def test_path(
    path: str,
    verbose: bool = False,
    watch: bool = False,
    multiple: bool = False,
) -> bool:
    """Check the path for linting errors.
    :param path: The path to check.
    """
    extra_args = []
    if multiple:
        extra_args = ["-n", str(cpu_count())]
    command = CommandExecutor(
        [
            "poetry",
            "run",
            "pytest",
            str(path),
            "-vv",
        ]
        + (["-w"] if watch else [])
        + extra_args
    )
    return command.execute(verbose=verbose, stream=True)

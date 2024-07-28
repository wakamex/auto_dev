"""
Module for testing the project.
"""
from multiprocessing import cpu_count
from .cli_executor import CommandExecutor


def test_path(path: str, verbose: bool = False) -> bool:
    """
    Check the path for linting errors.
    :param path: The path to check
    """
    available_cores = cpu_count()
    command = CommandExecutor(
        [
            "poetry",
            "run",
            "pytest",
            str(path),
            "-vv",
            "-n",
            str(available_cores),
        ]
    )
    result = command.execute(verbose=verbose, stream=True)
    return result

"""
Test the augmenter.
"""
import pytest

from auto_dev.commands.augment import LoggingScaffolder


@pytest.fixture
def logging_scaffolder():
    """Logging scaffolder fixture."""
    return LoggingScaffolder()


def test_logging_scaffolder_options(logging_scaffolder):
    """test the logging scaffolder."""
    options = logging_scaffolder.options()
    assert options == ["console", "http", "logfile"]


def test_logging_scaffolder_scaffold(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["console"])
    assert "console" in scaffold
    assert "http" not in scaffold


def test_logging_scaffolder_scaffold_all(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["all"])
    assert "console" in scaffold
    assert "http" in scaffold
    assert "logfile" in scaffold


def test_logging_scaffolder_scaffold_bad_handler(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["bad"])
    assert scaffold is None
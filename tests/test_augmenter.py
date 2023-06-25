"""
Test the augmenter.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from auto_dev.commands.augment import LoggingScaffolder


@pytest.fixture
def isolated_filesystem():
    """Fixture for invoking command-line interfaces."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = f"{tmpdir}/dir"
        shutil.copytree(Path(cwd), test_dir)
        os.chdir(test_dir)
        Path("aea-config.yaml").write_text("author: aea-config.yaml\nversion: 1.0.0\n", encoding="utf-8")
        yield test_dir
    os.chdir(cwd)


@pytest.fixture
def logging_scaffolder(isolated_filesystem):
    """Logging scaffolder fixture."""
    del isolated_filesystem
    return LoggingScaffolder()


def test_logging_scaffolder_scaffold_all(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["all"])
    assert "console" in scaffold['logging_config']['handlers']
    assert "http" in scaffold['logging_config']['handlers']
    assert "logfile" in scaffold['logging_config']['handlers']


def test_logging_scaffolder_scaffold(logging_scaffolder):
    """test the logging scaffolder."""
    scaffold = logging_scaffolder.scaffold(["console"])
    assert "console" in scaffold['logging_config']['handlers']
    assert "http" not in scaffold['logging_config']['handlers']
    assert "logfile" not in scaffold['logging_config']['handlers']


def test_logging_scaffolder_scaffold_bad_handler(logging_scaffolder):
    """test the logging scaffolder."""
    with pytest.raises(ValueError):
        logging_scaffolder.scaffold(["bad"])

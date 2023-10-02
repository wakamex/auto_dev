"""
Tests for the documentation.
"""
from logging import getLogger
import os
from pathlib import Path
from auto_dev.cli_executor import CommandExecutor
import pytest

def extract_code_blocks(doc):
    """Extract the code blocks from the documentation."""
    with open(doc, "r") as f:
        lines = f.readlines()
    code_blocks = []
    code_block = []
    in_code_block = False
    for line in lines:
        if in_code_block:
            if line.startswith("```"):
                in_code_block = False
                code_blocks.append("".join(code_block))
                code_block = []
            else:
                cleaned_line = line.strip()
                code_block.append(cleaned_line)
        else:
            if line.startswith("```bash"):
                in_code_block = True
    return code_blocks


# we test the documents works.

documenation = [
    "docs/fsm.md"
]
logger = getLogger()

@pytest.mark.parametrize("doc", documenation)
def test_documentation(doc):
    """Test the documentation."""
    assert Path(doc).exists()

# extract the code blocks from the documentation.

@pytest.mark.parametrize("doc", documenation)
def test_doc_code_execution(doc):
    """Test the documentation."""
    commands = extract_code_blocks(doc)

    # execute the commands.
    for command in commands:
        logger.info(f"Executing command:\n\"\"\n{command}\n\"\"")
        # really not ideal, but cd is shell command, and were not passing the entire shell command.
        if command.startswith("cd"):
            os.chdir(command.split(" ")[1])
        else:
            executor = CommandExecutor(command)
            assert executor.execute(stream=True, shell=True), f"Command failed: {command}"

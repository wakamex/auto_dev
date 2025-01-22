"""Tests for the publish service and command."""

from pathlib import Path

import pytest
from aea.configurations.base import PublicId

from auto_dev.enums import LockType
from auto_dev.utils import change_dir
from auto_dev.constants import DEFAULT_AUTHOR, DEFAULT_AGENT_NAME, AGENT_PUBLISHED_SUCCESS_MSG
from auto_dev.exceptions import OperationError


def test_force_removes_package(publish_service, test_packages_filesystem, dummy_agent_default):
    """Test that force flag properly removes existing package."""
    assert test_packages_filesystem
    assert dummy_agent_default
    assert Path("aea-config.yaml").exists()

    # First publish
    publish_service.publish_agent()
    packages_path = Path("..") / "packages" / DEFAULT_AUTHOR / "agents" / DEFAULT_AGENT_NAME
    assert packages_path.exists()

    # Add a test file to verify it gets removed
    test_file = packages_path / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()

    # Force publish should remove the entire package directory
    publish_service.publish_agent(force=True)
    assert packages_path.exists()  # Package should be recreated
    assert (packages_path / "aea-config.yaml").exists()
    assert not test_file.exists()  # Test file should be gone

    # Add test file again and verify force publish with lock also removes it
    test_file.write_text("test content")
    assert test_file.exists()
    publish_service.publish_agent(force=True, lock_type=LockType.DEV)
    assert not test_file.exists()  # Test file should be gone again
    assert packages_path.exists()  # Package should be recreated
    assert (packages_path / "aea-config.yaml").exists()


def test_publish_command_messages(cli_runner, test_packages_filesystem, dummy_agent_default):
    """Test publish command output messages."""
    assert test_packages_filesystem
    assert dummy_agent_default
    assert Path("aea-config.yaml").exists()

    # Test invalid ID message first (before any publishing)
    cmd = ["adev", "-v", "publish", "invalid_id"]
    runner = cli_runner(cmd)
    result = runner.execute()
    assert not result
    assert "Invalid value for '[PUBLIC_ID]': invalid_id" in runner.output

    # Test successful first publish
    cmd = ["adev", "-v", "publish"]
    runner = cli_runner(cmd)
    result = runner.execute()
    assert result
    assert AGENT_PUBLISHED_SUCCESS_MSG in runner.output

    # Test package exists error without force
    cmd = ["adev", "-v", "publish"]
    runner = cli_runner(cmd)
    result = runner.execute()
    assert not result
    assert "already exists" in runner.output

    # Test force publish succeeds by removing existing package
    packages_path = Path("..") / "packages" / DEFAULT_AUTHOR / "agents" / DEFAULT_AGENT_NAME
    test_file = packages_path / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()

    cmd = ["adev", "-v", "publish", "--force"]
    runner = cli_runner(cmd)
    result = runner.execute()
    assert result
    assert AGENT_PUBLISHED_SUCCESS_MSG in runner.output
    assert not test_file.exists()  # Test file should be gone


def test_publish_error_messages(publish_service, test_packages_filesystem, dummy_agent_default):
    """Test error messages during publishing."""
    assert test_packages_filesystem
    assert dummy_agent_default
    assert Path("aea-config.yaml").exists()

    # First publish to create package
    publish_service.publish_agent()

    # Test package exists error
    with pytest.raises(OperationError, match="Package already exists .* Use --force to overwrite"):
        publish_service.publish_agent()

    # Test wrong directory error
    with pytest.raises(OperationError, match="Not in an agent directory"):
        with change_dir(".."):
            publish_service.publish_agent()

    # Test non-existent directory error
    with pytest.raises(OperationError, match="Agent directory .* does not exist"):
        publish_service.publish_agent(PublicId(DEFAULT_AUTHOR, "nonexistent", "0.1.0"))


def test_publish_package_creation(publish_service, test_packages_filesystem, dummy_agent_default):
    """Test package creation and structure."""
    assert test_packages_filesystem
    assert dummy_agent_default
    assert Path("aea-config.yaml").exists()

    # Test basic publish creates correct package structure
    publish_service.publish_agent()

    packages_path = Path("..") / "packages" / DEFAULT_AUTHOR / "agents" / DEFAULT_AGENT_NAME
    assert packages_path.exists()
    assert (packages_path / "aea-config.yaml").exists()

    # Add a test file to verify it gets removed
    test_file = packages_path / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()

    # Force publish should remove the entire package directory
    publish_service.publish_agent(force=True)
    assert packages_path.exists()  # Package should be recreated
    assert (packages_path / "aea-config.yaml").exists()
    assert not test_file.exists()  # Test file should be gone


def test_publish_package_locking(publish_service, test_packages_filesystem, dummy_agent_default):
    """Test package locking functionality."""
    assert test_packages_filesystem
    assert dummy_agent_default
    assert Path("aea-config.yaml").exists()

    packages_path = Path("..") / "packages" / DEFAULT_AUTHOR / "agents" / DEFAULT_AGENT_NAME
    lock_file = Path("..") / "packages" / "packages.json"

    # Test publish with lock creates lock file
    publish_service.publish_agent(None, lock_type=LockType.DEV)
    assert packages_path.exists()
    assert (packages_path / "aea-config.yaml").exists()
    assert lock_file.exists()

    # Add a test file to verify force removes it
    test_file = packages_path / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()

    # Force publish with lock should remove and recreate everything
    publish_service.publish_agent(None, lock_type=LockType.DEV, force=True)
    assert packages_path.exists()
    assert (packages_path / "aea-config.yaml").exists()
    assert not test_file.exists()  # Test file should be gone
    assert lock_file.exists()  # Lock file should still exist

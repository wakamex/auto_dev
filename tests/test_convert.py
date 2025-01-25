"""Tests for the convert command."""

from pathlib import Path

import pytest
from aea.configurations.base import PublicId
from aea.configurations.constants import PACKAGES, SERVICES

from auto_dev.constants import DEFAULT_PUBLIC_ID
from auto_dev.commands.convert import ConvertCliTool


@pytest.mark.parametrize(
    ("agent_public_id", "service_public_id"),
    [
        (str(DEFAULT_PUBLIC_ID), str(DEFAULT_PUBLIC_ID)),
        (str(DEFAULT_PUBLIC_ID), "author/service"),
        (str(DEFAULT_PUBLIC_ID), "jim/jones"),
    ],
)
def test_convert_agent_to_service(dummy_agent_tim, agent_public_id, service_public_id, test_packages_filesystem):
    """Test the convert agent to service command."""
    assert dummy_agent_tim, "Dummy agent not created."
    assert test_packages_filesystem, "Test packages filesystem not created."
    convert = ConvertCliTool(agent_public_id, service_public_id)
    result = convert.generate()
    output_public_id = PublicId.from_str(service_public_id)
    assert (Path(PACKAGES) / output_public_id.author / SERVICES / output_public_id.name).exists()
    assert result


@pytest.mark.parametrize(
    ("agent_public_id", "service_public_id"),
    [
        (str(DEFAULT_PUBLIC_ID), str(DEFAULT_PUBLIC_ID)),
    ],
)
def test_force(dummy_agent_tim, agent_public_id, service_public_id, test_packages_filesystem):
    """Test the convert agent to service command."""
    assert dummy_agent_tim, "Dummy agent not created."
    assert test_packages_filesystem, "Test packages filesystem not created."
    convert = ConvertCliTool(agent_public_id, service_public_id)
    result = convert.generate()
    output_public_id = PublicId.from_str(service_public_id)
    assert (Path(PACKAGES) / output_public_id.author / SERVICES / output_public_id.name).exists()
    assert result
    # Test force
    convert = ConvertCliTool(agent_public_id, service_public_id)
    with pytest.raises(FileExistsError):
        result = convert.generate()
    assert convert.generate(force=True)

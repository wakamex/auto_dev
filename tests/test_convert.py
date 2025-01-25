"""Tests for the convert command."""

import pytest

from auto_dev.constants import DEFAULT_PUBLIC_ID
from auto_dev.commands.convert import ConvertCliTool


@pytest.mark.parametrize(
    ("agent_public_id", "service_public_id"),
    [
        (str(DEFAULT_PUBLIC_ID), str(DEFAULT_PUBLIC_ID)),
    ],
)
def test_convert_agent_to_service(dummy_agent_tim, agent_public_id, service_public_id, test_packages_filesystem):
    """Test the convert agent to service command."""
    assert dummy_agent_tim, "Dummy agent not created."
    assert test_packages_filesystem, "Test packages filesystem not created."
    convert = ConvertCliTool(agent_public_id, service_public_id)
    result = convert.generate()
    assert result

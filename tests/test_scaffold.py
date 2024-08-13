"""Tests for the scaffold command."""

import sys
import subprocess
from pathlib import Path

import yaml
import pytest
from aea.cli import cli as aea_cli
from aea.configurations.base import PublicId

from auto_dev.cli import cli
from auto_dev.utils import get_logger
from auto_dev.constants import DEFAULT_ENCODING
from auto_dev.handler.scaffolder import HandlerScaffoldBuilder
from auto_dev.protocols.scaffolder import read_protocol


FSM_SPEC = Path("auto_dev/data/fsm/fsm_specification.yaml").absolute()


class Mockers:
    """Class containing mock objects for testing"""

    class MockRunner:
        """Mock runner for testing scaffold commands"""

        def __init__(self):
            self.return_code = 0
            self.output = ""


def get_yaml_files(directory):
    """Get all yaml files in a directory."""
    return [str(f) for f in Path(directory).glob("*.yaml")]


def get_paths_from_yaml(yaml_file):
    """Get all paths from a yaml file."""
    with open(yaml_file, encoding=DEFAULT_ENCODING) as f:
        spec = yaml.safe_load(f)

    paths = []
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            handler_name = path.replace("{", "").replace("}", "")
            handler_name = f"handle_{method.lower()}_{handler_name.lstrip('/').replace('/', '_')}"
            paths.append(handler_name)
    return paths


@pytest.mark.skip(reason="Needs chain contracts update")
@pytest.mark.parametrize("spec", [None, FSM_SPEC])
def test_scaffold_fsm_with_aea_run(cli_runner, spec, dummy_agent_tim):
    """Test scaffold base FSM upto `aea run`."""

    command = ["adev", "scaffold", "fsm"]
    if spec:
        command.extend(["--spec", str(spec)])

    dummy_agent_tim.exists()
    runner = cli_runner(command)
    result = runner.execute()
    assert runner.exit_code == 0, runner.output

    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "abstract_round_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "registration_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "reset_pause_abci").exists()
    assert (Path.cwd() / "vendor" / "valory" / "skills" / "termination_abci").exists()

    cmd = ["aea", "run"]
    runner = cli_runner(cmd)
    result = runner.execute()
    assert runner.exit_code == 1, runner.output
    assert "An error occurred during instantiation of connection valory" in result.output


@pytest.mark.skip(reason="Needs chain contracts update")
def test_scaffold_protocol(cli_runner, dummy_agent_tim, caplog):
    """Test scaffold protocol."""

    path = Path.cwd() / ".." / "tests" / "data" / "dummy_protocol.yaml"
    command = ["scaffold", "protocol", str(path)]
    result = cli_runner.invoke(cli, command)

    assert result.exit_code == 0, result.output
    assert f"New protocol scaffolded at {dummy_agent_tim}" in caplog.text

    protocol = read_protocol(str(path))
    original_content = path.read_text(encoding=DEFAULT_ENCODING)
    readme_path = dummy_agent_tim / "protocols" / protocol.metadata["name"] / "README.md"
    assert original_content in readme_path.read_text(encoding=DEFAULT_ENCODING)


def test_scaffold_handler(dummy_agent_tim, openapi_test_case):
    """Test scaffold handler"""

    openapi_file, expected_handlers = openapi_test_case
    openapi_spec_path, public_id = prepare_scaffold_inputs(openapi_file, dummy_agent_tim)

    runner = run_scaffold_command(
        openapi_spec_path=openapi_spec_path, public_id=public_id, new_skill=True, auto_confirm=True
    )

    assert runner.return_code == 0, runner.output

    skill_path = Path(dummy_agent_tim) / "skills" / public_id.name
    verify_scaffolded_files(skill_path)
    verify_handlers_content(skill_path, expected_handlers)
    verify_dynamic_handlers(openapi_spec_path, expected_handlers, openapi_file)
    verify_skill_yaml(skill_path)


def prepare_scaffold_inputs(openapi_file, dummy_agent_tim):
    """Prepare inputs for scaffold command."""
    assert Path.cwd() == Path(dummy_agent_tim)
    openapi_spec_path = f"../tests/data/openapi_examples/{openapi_file}"
    skill_name = f"skill_{openapi_file.replace('.yaml', '').replace('.yml', '')}"
    sanitized_skill_name = skill_name.replace("-", "_").replace(" ", "_")
    public_id = PublicId("dummy_author", sanitized_skill_name, "0.1.0")
    return openapi_spec_path, public_id


def run_scaffold_command(openapi_spec_path, public_id, new_skill, auto_confirm):
    """Run scaffold command"""
    logger = get_logger()
    verbose = True

    scaffolder = (
        HandlerScaffoldBuilder()
        .create_scaffolder(
            openapi_spec_path,
            public_id,
            logger,
            verbose,
            new_skill=new_skill,
            auto_confirm=auto_confirm,
        )
        .build()
    )

    scaffolder.scaffold()
    return Mockers.MockRunner()


def verify_scaffolded_files(skill_path):
    """Verify if expected files are created/modified."""
    assert not (skill_path / "behaviours.py").exists()
    assert (skill_path / "strategy.py").exists()
    assert (skill_path / "dialogues.py").exists()
    assert (skill_path / "handlers.py").exists()


def verify_handlers_content(skill_path, expected_handlers):
    """Verify content of handlers.py."""
    handlers_content = (skill_path / "handlers.py").read_text()
    assert "class HttpHandler(Handler):" in handlers_content
    for handler in expected_handlers:
        assert f"def {handler}(" in handlers_content, f"Handler method for '{handler}' not found"


def verify_dynamic_handlers(openapi_spec_path, expected_handlers, openapi_file):
    """Verify dynamically generated handlers."""
    dynamic_handlers = get_paths_from_yaml(openapi_spec_path)
    assert set(expected_handlers) == set(
        dynamic_handlers
    ), f"Mismatch between expected and dynamically generated handlers for {openapi_file}"


def verify_skill_yaml(skill_path):
    """Verify content of skill.yaml."""
    with open(skill_path / "skill.yaml", encoding=DEFAULT_ENCODING) as f:
        skill_yaml = yaml.safe_load(f)
    assert "eightballer/http:0.1.0" in skill_yaml["protocols"][0]
    assert "behaviours" in skill_yaml
    assert not skill_yaml["behaviours"]
    assert "handlers" in skill_yaml
    assert "http_handler" in skill_yaml["handlers"]
    assert "models" in skill_yaml
    assert "strategy" in skill_yaml["models"]
    assert "http_dialogues" in skill_yaml["models"]


@pytest.mark.skip(reason="Needs chain contracts update")
class TestScaffoldConnection:
    """Test scaffold connection."""

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""

        cls.protocol_id = "zarathustra/sql_crud:0.1.0"
        cls.protocol_path = "../tests/data/crud_protocol.yaml"

    def test_no_name_provided(self, cli_runner, dummy_agent_tim):
        """Test no name provided."""

        assert Path.cwd() == Path(dummy_agent_tim)

        result = cli_runner.invoke(cli, f"scaffold protocol {self.protocol_path}")
        assert result.exit_code == 0, result.output

        result = cli_runner.invoke(cli, ["scaffold", "connection"])
        assert result.exit_code == 2, result.output
        assert "Missing argument 'NAME'" in result.output

    def test_scaffold_with_spec_readme(self, cli_runner, dummy_agent_tim, caplog):
        """Test scaffold protocol specification in README."""

        result = cli_runner.invoke(cli, f"scaffold protocol {self.protocol_path}")
        assert result.exit_code == 0, result.output

        result = cli_runner.invoke(cli, ["scaffold", "connection", "my_connection", "--protocol", self.protocol_id])
        assert result.exit_code == 0, result.output
        assert f"Read protocol specification: {self.protocol_path}" in caplog.text
        assert f"New connection scaffolded at {dummy_agent_tim}" in caplog.text

    def test_scaffold_with_python(self, cli_runner, dummy_agent_tim, caplog):
        """Test scaffold with python run for correct imports."""

        result = cli_runner.invoke(cli, f"scaffold protocol {self.protocol_path}")
        assert result.exit_code == 0, result.output

        result = cli_runner.invoke(cli, ["scaffold", "connection", "my_connection", "--protocol", self.protocol_id])
        assert result.exit_code == 0, result.output
        assert f"New connection scaffolded at {dummy_agent_tim}" in caplog.text

        result = cli_runner.invoke(aea_cli, "remove-key ethereum".split())
        assert result.exit_code == 0, result.output

        result = cli_runner.invoke(aea_cli, "publish --push-missing --local".split())
        assert result.exit_code == 0, result.output

        connection_dir = Path("../packages/zarathustra/connections/my_connection")
        connection_path = connection_dir / "connection.py"
        test_connection_path = connection_dir / "tests" / "test_connection.py"

        for path in (connection_path, test_connection_path):
            result = subprocess.run([sys.executable, path], shell=True, check=True, capture_output=True)
            assert result.returncode == 0, result.stderr

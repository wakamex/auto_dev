"""Handler scaffolder."""
# ruff: noqa: E501

import re
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from aea.configurations.base import PublicId

from auto_dev.utils import change_dir, get_logger, validate_openapi_spec, camel_to_snake
from auto_dev.constants import DEFAULT_ENCODING, JINJA_TEMPLATE_FOLDER
from auto_dev.cli_executor import CommandExecutor
from auto_dev.commands.metadata import read_yaml_file


HTTP_PROTOCOL = "eightballer/http:0.1.0:bafybeihmhy6ax5uyjt7yxppn4viqswibcs5lsjhl3kvrsesorqe2u44jcm"


class ScaffolderConfig:
    """Handler Scaffolder."""

    def __init__(
        self,
        spec_file_path: str,
        public_id,
        verbose: bool = True,
        new_skill: bool = False,
        auto_confirm: bool = False,
    ):
        """Initialize HandlerScaffolder."""
        self.verbose = verbose
        self.spec_file_path = spec_file_path
        self.author = public_id.author
        self.output = public_id.name
        self.verbose = verbose
        self.new_skill = new_skill
        self.auto_confirm = auto_confirm


class HandlerScaffolder:
    """Handler Scaffolder."""

    def __init__(
        self,
        config: ScaffolderConfig,
        logger,
    ):
        """Initialize HandlerScaffolder."""

        self.config = config
        self.logger = logger or get_logger()
        self.handler_code = ""
        self.jinja_env = Environment(
            loader=FileSystemLoader(Path(JINJA_TEMPLATE_FOLDER) / "customs"),
            autoescape=False,  # noqa: S701
        )
        self.jinja_env.globals["zip"] = zip

    def scaffold(self):
        """Scaffold the handler."""

        if not self.present_actions():
            return

        if self.config.new_skill:
            self.create_new_skill()

        self.generate_handler()

        with self._change_dir():
            self.save_handler(self.config.output / Path("handlers.py"))
            self.update_skill_yaml(Path("skill.yaml"))
            self.move_and_update_my_model()
            self.remove_behaviours()
            self.create_dialogues()

        self.fingerprint()
        self.aea_install()
        self.add_protocol()

    def _change_dir(self):
        return change_dir(Path("skills") / self.config.output)

    def create_new_skill(self) -> None:
        """Create a new skill."""
        skill_cmd = f"aea scaffold skill {self.config.output}".split(" ")
        if not CommandExecutor(skill_cmd).execute(verbose=self.config.verbose):
            msg = "Failed to scaffold skill."
            raise ValueError(msg)

    def generate_handler(self) -> None:
        """Generate handler."""
        openapi_spec = read_yaml_file(self.config.spec_file_path)
        if not validate_openapi_spec(openapi_spec, self.logger):
            raise SystemExit(1)

        if not all(path.startswith("/api") for path in openapi_spec.get("paths", {})):
            self.logger.error("All paths in the OpenAPI spec must start with '/api'")
            raise SystemExit(1)

        schemas = set()
        for path, path_spec in openapi_spec.get("paths", {}).items():
            # For GET responses
            if "get" in path_spec and "{" not in path:
                schema_ref = path_spec["get"]["responses"]["200"]["content"]["application/json"]["schema"]["items"].get("$ref")
                if schema_ref:
                    schema_name = schema_ref.split("/")[-1]
                    schemas.add(schema_name)

            # For POST request bodies
            if "post" in path_spec:
                request_body = path_spec["post"].get("requestBody", {})
                content = request_body.get("content", {}).get("application/json", {})
                schema_def = content.get("schema", {})
                schema_ref = schema_def.get("$ref")
                if schema_ref:
                    schema_name = schema_ref.split("/")[-1]
                    schemas.add(schema_name)

        # Convert schema names to snake_case for consistency
        schema_filenames = [camel_to_snake(schema) + "_dao" for schema in schemas]

        handler_methods = []

        def extract_schema(operation, method):
            if method.lower() == 'post':
                request_body = operation.get('requestBody', {})
                content = request_body.get('content', {}).get('application/json', {})
                schema_def = content.get('schema', {})
                schema_ref = schema_def.get('$ref')
                return schema_ref.split("/")[-1] if schema_ref else None
            else:
                if "responses" not in operation:
                    return None

                success_response = operation["responses"].get("200", {})
                content = success_response.get("content", {}).get("application/json", {})
                schema_def = content.get("schema", {})

                if schema_def.get("type") == "array":
                    schema_ref = schema_def.get("items", {}).get("$ref")
                else:
                    schema_ref = schema_def.get("$ref")

                return schema_ref.split("/")[-1] if schema_ref else None

        def classify_post_operation(path, operation):
            keywords = operation.get('operationId', '') + ' ' + operation.get('summary', '') + ' ' + operation.get('description', '')
            keywords = keywords.lower()

            if '{' in path:
                return 'update'
            elif any(word in keywords for word in ['create', 'new']):
                return 'insert'
            elif any(word in keywords for word in ['update', 'modify']):
                return 'update'
            else:
                return 'other'

        for path, path_item in openapi_spec["paths"].items():
            for method, operation in path_item.items():
                method_name = self.generate_method_name(method, path)
                path_params = [
                    param.strip("{}") for param in path.split("/") if param.startswith("{") and param.endswith("}")
                ]

                schema = extract_schema(operation, method)

                operation_type = 'other'
                if method.lower() == 'post':
                    operation_type = classify_post_operation(path, operation)

                method_template = self.jinja_env.get_template("method_template.jinja")
                method_code = method_template.render(
                    method_name=method_name,
                    method=method,
                    path=path,
                    path_params=path_params,
                    schema=schema,
                    operation_type=operation_type
                )

                handler_methods.append(method_code)

        all_methods = "\n\n".join(handler_methods)

        header_template = self.jinja_env.get_template("handler_header.jinja")
        handler_code = header_template.render(
            author=self.config.author,
            skill_name=self.config.output,
            schemas=schemas,
            schema_filenames=schema_filenames
        )

        main_handler_template = self.jinja_env.get_template("main_handler.jinja")
        unexpected_message_handler_template = self.jinja_env.get_template("unexpected_message_handler.jinja")

        path_params = set()
        for path in openapi_spec.get("paths", {}):
            path_params.update(re.findall(r"\{(\w+)\}", path))

        main_handler = main_handler_template.render(
            all_methods=all_methods,
            unexpected_message_handler=unexpected_message_handler_template.render(),
            path_params=path_params,
        )

        handler_code += main_handler
        return handler_code

    def generate_method_name(self, http_method, path):
        """Generate method name."""
        method_name = "handle_" + http_method.lower()
        parts = [part for part in path.strip("/").split("/") if part]
        name_parts = []
        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                param_name = part.strip("{}")
                param_name = self.sanitize_identifier(param_name)
                name_parts.append("by_" + param_name)
            else:
                part_name = self.sanitize_identifier(part)
                name_parts.append(part_name)
        method_name += "_" + "_".join(name_parts)
        return method_name

    def save_handler(self, path) -> None:
        """Save handler to file."""
        path = Path("handlers.py")
        with open(path, "w", encoding=DEFAULT_ENCODING) as f:
            try:
                f.write(self.handler_code)
            except Exception as e:
                msg = f"Error writing to file: {e}"
                raise ValueError(msg) from e

    def update_skill_yaml(self, file) -> None:
        """Update the skill.yaml file."""
        skill_yaml = read_yaml_file(file)

        skill_yaml["protocols"] = [HTTP_PROTOCOL]
        skill_yaml["behaviours"] = {}
        del skill_yaml["handlers"]
        skill_yaml["handlers"] = {
            "http_handler": {
                "args": {},
                "class_name": "HttpHandler",
            }
        }
        skill_yaml["models"] = {
            "strategy": {
                "args": {},
                "class_name": "Strategy",
            },
            "http_dialogues": {
                "args": {},
                "class_name": "HttpDialogues",
            },
        }

        with open(file, "w", encoding=DEFAULT_ENCODING) as f:
            yaml.safe_dump(skill_yaml, f, sort_keys=False)

    def move_and_update_my_model(self) -> None:
        """Reads in the my_model.py file and updates it.
        We replace the name MyModel with the name Strategy.
        """
        my_model_file = Path("my_model.py")
        strategy_file = Path("strategy.py")

        if my_model_file.exists():
            strategy_code = my_model_file.read_text(encoding=DEFAULT_ENCODING)
            strategy_code = strategy_code.replace("MyModel", "Strategy")

            if self.confirm_action(
                f"Are you sure you want to remove the file '{my_model_file}' and create '{strategy_file}'?"
            ):
                my_model_file.unlink()
                strategy_file.write_text(strategy_code, encoding=DEFAULT_ENCODING)
            else:
                pass

    def remove_behaviours(self) -> None:
        """Remove the behaviours.py file."""
        behaviours_file = Path("behaviours.py")
        if behaviours_file.exists():
            if self.confirm_action(f"Are you sure you want to remove the file '{behaviours_file}'?"):
                behaviours_file.unlink()
            else:
                pass
        else:
            pass

    def create_dialogues(self) -> None:
        """Create the dialogues."""
        dialogues_file = "dialogues.py"
        dialogues_template = self.jinja_env.get_template("dialogues.jinja")
        with open(dialogues_file, "w", encoding=DEFAULT_ENCODING) as f:
            f.write(dialogues_template.render())

    def fingerprint(self):
        """Fingerprint the skill."""
        skill_id = PublicId(self.config.author, self.config.output, "0.1.0")
        cli_executor = CommandExecutor(f"aea fingerprint skill {skill_id}".split())
        result = cli_executor.execute(verbose=True)
        if not result:
            msg = f"Fingerprinting failed: {skill_id}"
            raise ValueError(msg)

    def aea_install(self) -> None:
        """Install the aea."""
        install_cmd = ["aea", "install"]
        if not CommandExecutor(install_cmd).execute(verbose=self.config.verbose):
            msg = f"Failed to execute {install_cmd}."
            raise ValueError(msg)

    def add_protocol(self):
        """Add the protocol."""
        protocol_cmd = f"aea add protocol {HTTP_PROTOCOL}".split(" ")
        if not CommandExecutor(protocol_cmd).execute(verbose=self.config.verbose):
            msg = f"Failed to add {HTTP_PROTOCOL}."
            raise ValueError(msg)

    def confirm_action(self, message):
        """Prompt the user for confirmation before performing an action."""
        if self.config.auto_confirm:
            self.logger.info(f"Auto confirming: {message}")
            return True
        response = input(f"{message} (y/n): ").lower().strip()
        return response in {"y", "yes"}

    def present_actions(self):
        """Present the scaffold summary."""
        actions = [
            f"Generating handler based on OpenAPI spec: {self.config.spec_file_path}",
            f"Saving handler to: skills/{self.config.output}/handlers.py",
            f"Updating skill.yaml in skills/{self.config.output}/",
            f"Moving and updating my_model.py to strategy.py in: skills/{self.config.output}/",
            f"Removing behaviours.py in: skills/{self.config.output}/",
            f"Creating dialogues.py in: skills/{self.config.output}/",
            "Fingerprinting the skill",
            "Running 'aea install'",
            f"Adding HTTP protocol: {HTTP_PROTOCOL}",
        ]

        if self.config.new_skill:
            actions.insert(0, f"Creating new skill: {self.config.output}")

        self.logger.info("The following actions will be performed:")
        for i, action in enumerate(actions, 1):
            self.logger.info(f"{i}. {action}")

        if not self.config.auto_confirm:
            confirm = input("Do you want to proceed? (y/n): ").lower().strip()
            if confirm not in {"y", "yes"}:
                self.logger.info("Scaffolding cancelled.")
                return False

        return True

    def sanitize_identifier(self, name: str) -> str:
        """Sanitize the identifier."""
        name = re.sub(r"[^0-9a-zA-Z_]", "_", name)
        if name and name[0].isdigit():
            name = "_" + name
        return name.lower()


class HandlerScaffoldBuilder:
    """Builder for HandlerScaffolder."""

    def __init__(self):
        """Initialize HandlerScaffoldBuilder."""
        self.config = None
        self.logger = None

    def create_scaffolder(
        self,
        spec_file_path: str,
        public_id,
        logger,
        verbose: bool = True,
        new_skill: bool = False,
        auto_confirm: bool = False,
    ):
        """Initialize HandlerScaffoldBuilder."""
        self.config = ScaffolderConfig(spec_file_path, public_id, verbose, new_skill, auto_confirm)
        self.logger = logger
        return self

    def build(self) -> HandlerScaffolder:
        """Build the scaffolder."""
        if not self.config:
            msg = "Scaffolder not initialized. Call create_scaffolder first."
            raise ValueError(msg)
        return HandlerScaffolder(self.config, self.logger)

"""Handler scaffolder."""
# ruff: noqa: E501

import re
from typing import Any, Union, Optional
from pathlib import Path
from collections import defaultdict

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic import Field, BaseModel, ValidationError
from aea.configurations.base import PublicId

from auto_dev.enums import FileType
from auto_dev.utils import change_dir, get_logger, write_to_file, camel_to_snake, validate_openapi_spec
from auto_dev.constants import DEFAULT_ENCODING, JINJA_TEMPLATE_FOLDER
from auto_dev.cli_executor import CommandExecutor
from auto_dev.commands.metadata import read_yaml_file


class Reference(BaseModel):
    """OpenAPI Reference Object."""
    ref: str = Field(alias="$ref")

    def resolve(self, root_doc: Any) -> Any:
        """Resolve the reference."""
        parts = self.ref.split("/")[1:]
        current = root_doc
        for part in parts:
            current = getattr(current, part, None) or current.get(part)
        return current


class Schema(BaseModel):
    """OpenAPI Schema Object."""
    type: Optional[str] = None
    properties: Optional[dict[str, Union['Schema', Reference]]] = None
    items: Optional[Union['Schema', Reference]] = None
    required: Optional[list[str]] = None
    description: Optional[str] = None
    title: Optional[str] = None
    x_persistent: Optional[bool] = Field(default=None, alias="x-persistent")

    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


class Parameter(BaseModel):
    """OpenAPI Parameter Object."""
    name: str
    param_in: str = Field(alias="in")
    description: Optional[str] = None
    required: bool = False
    schema_: Optional[dict] = Field(default=None, alias="schema")


class MediaTypeObject(BaseModel):
    """OpenAPI Media Type Object."""
    media_type_schema: Optional[Union[dict, Reference]] = Field(default=None, alias="schema")


class RequestBody(BaseModel):
    """OpenAPI Request Body Object."""
    description: Optional[str] = None
    content: dict[str, MediaTypeObject]
    required: bool = False


class Response(BaseModel):
    """OpenAPI Response Object."""
    description: str
    content: Optional[dict[str, MediaTypeObject]] = None
    headers: Optional[dict[str, Any]] = None


class Operation(BaseModel):
    """OpenAPI Operation Object."""
    tags: Optional[list[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    operationId: Optional[str] = None
    parameters: Optional[list[Parameter]] = None
    requestBody: Optional[RequestBody] = None
    responses: dict[str, Response]


class PathItem(BaseModel):
    """OpenAPI Path Item Object."""
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    delete: Optional[Operation] = None
    patch: Optional[Operation] = None
    parameters: Optional[list[Parameter]] = None


class Components(BaseModel):
    """OpenAPI Components Object."""
    schemas: Optional[dict[str, Union[Schema, Reference]]] = None


class OpenAPI(BaseModel):
    """OpenAPI Object."""
    openapi: str
    info: dict[str, Any]
    paths: dict[str, Union[PathItem, Reference]]
    components: Optional[Components] = None


Schema.model_rebuild()


class ScaffolderConfig(BaseModel):
    """Configuration for the Handler Scaffolder."""
    spec_file_path: str
    public_id: PublicId
    verbose: bool = True
    new_skill: bool = False
    auto_confirm: bool = False
    use_daos: bool = False

    # Allow arbitrary types for public_id
    model_config = {
        "arbitrary_types_allowed": True
    }


class CrudOperation:
    """Crud operation."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    OTHER = "other"


class ScaffolderError(Exception):
    """Scaffolder error."""
    pass


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

        try:
            self.generate_handler()
            with self._change_dir():
                self.save_handler()
                self.update_skill_yaml(Path("skill.yaml"))
                self.move_and_update_my_model()
                self.remove_behaviours()
                self.create_dialogues()
                self.create_exceptions()
            self.fingerprint()
            self.aea_install()
        except ScaffolderError as e:
            self.logger.exception(f"Scaffolding failed: {e}")
            raise SystemExit(1) from e

    def _change_dir(self):
        return change_dir(Path("skills") / self.config.output)

    def create_new_skill(self) -> None:
        """Create a new skill."""
        skill_cmd = f"aea scaffold skill {self.config.output}".split(" ")
        if not CommandExecutor(skill_cmd).execute(verbose=self.config.verbose):
            msg = "Failed to scaffold skill."
            raise ScaffolderError(msg)

    def extract_schema(self, operation: Operation, persistent_schemas: list[str]) -> Optional[str]:
        """Extract the schema from the operation."""
        if not operation.responses:
            return None

        success_response = next(
            (
                resp
                for code, resp in operation.responses.items()
                if code in {"200", "201"}
            ),
            None,
        )
        if not success_response or not success_response.content:
            return None

        content = success_response.content.get("application/json")
        if not content or not content.media_type_schema:
            return None

        try:
            schema = parse_schema_like(content.media_type_schema)
            ref = None

            if isinstance(schema, Reference):
                ref = schema.ref
            elif isinstance(schema, Schema):
                if schema.type == "array" and schema.items:
                    items = parse_schema_like(schema.items)
                    if isinstance(items, Reference):
                        ref = items.ref
                elif hasattr(schema, "allOf"):
                    ref = next((s.ref for s in schema.allOf if isinstance(s, Reference)), None)
                elif hasattr(schema, "oneOf"):
                    ref = next((s.ref for s in schema.oneOf if isinstance(s, Reference)), None)

            return ref.split("/")[-1] if ref else None
        except AttributeError:
            self.logger.exception(f"Could not extract schema from response: {content}")
            return None

    def generate_handler(self) -> None:
        """Generate handler."""
        openapi_spec = load_openapi_spec(self.config.spec_file_path, self.logger)

        # TODO: Uncomment this when we have a way to validate the OpenAPI spec
        # if not validate_openapi_spec(openapi_spec, self.logger):
        #     msg = "OpenAPI specification validation failed"
        #     raise ScaffolderError(msg)

        # Check if all paths in the OpenAPI spec start with '/api'
        if not all(path.startswith("/api") for path in openapi_spec.paths):
            self.logger.error("All paths in the OpenAPI spec must start with '/api'")
            msg = "Invalid path prefixes in OpenAPI spec."
            raise ScaffolderError(msg)

        persistent_schemas = []
        if self.config.use_daos:
            persistent_schemas = self._get_persistent_schemas(openapi_spec)
            if not self._confirm_schemas(persistent_schemas):
                msg = "Schema confirmation failed."
                raise ScaffolderError(msg)

        handler_methods_info = get_crud_classification(openapi_spec, self.logger)
        handler_methods = self._generate_handler_methods_from_classifications(
            handler_methods_info,
            openapi_spec,
            persistent_schemas
        )
        if not handler_methods:
            self.logger.error("Error: handler_methods is None. Unable to process.")
            msg = "No handler methods generated."
            raise ScaffolderError(msg)

        self.handler_code = self._generate_handler_code(
            persistent_schemas,
            "\n\n".join(handler_methods),
            self._get_path_params(openapi_spec)
        )

        if not self.handler_code:
            self.logger.error("Error: handler_code is None. Unable to process.")
            msg = "Handler code generation failed."
            raise ScaffolderError(msg)

        return self.handler_code

    def _get_persistent_schemas(self, openapi_spec: OpenAPI) -> list[str]:
        """Retrieve the persistent schemas from the OpenAPI spec."""
        if not self.config.use_daos:
            return []
        schemas = openapi_spec.components.schemas if openapi_spec.components else {}
        persistent_schemas = []

        for schema_name, schema_data in schemas.items():
            schema = parse_schema_like(schema_data)
            is_persistent = False

            if isinstance(schema, dict):
                is_persistent = schema.get("x-persistent", False)
            elif isinstance(schema, Schema):
                is_persistent = schema.x_persistent
            elif hasattr(schema, "model_extra") and schema.model_extra:
                is_persistent = schema.model_extra.get("x-persistent", False)

            if is_persistent:
                persistent_schemas.append(schema_name)

        return persistent_schemas or self.identify_persistent_schemas(openapi_spec)

    def _confirm_schemas(self, persistent_schemas: list[str]) -> bool:
        """Confirm the persistent schemas."""
        self.logger.info("Persistent schemas:")
        for schema in persistent_schemas:
            self.logger.info(f"  - {schema}")
        if self.config.auto_confirm:
            self.logger.info("Auto confirming schema usage.")
            return True
        return input("Use these schemas for augmenting? (y/n): ").lower().strip() == "y"

    def _generate_handler_methods_from_classifications(
        self,
        classifications: list[dict],
        openapi_spec: OpenAPI,
        persistent_schemas: list[str]
    ) -> list[str]:
        """Generate handler methods from classifications."""
        handler_methods = []
        for classification in classifications:
            path = classification["path"]
            method = classification["method"]
            crud_type = classification["crud_type"]

            path_item = openapi_spec.paths[path]
            operation = getattr(path_item, method.lower())

            method_name = self.generate_method_name(method, path)
            path_params = [param.name for param in operation.parameters or [] if param.param_in == "path"]
            path_params_snake_case = [camel_to_snake(param) for param in path_params]
            schema = self.extract_schema(operation, persistent_schemas)

            response_info = self._extract_response_info(operation)

            error_responses = self._extract_error_responses(operation)

            method_code = self.jinja_env.get_template("method_template.jinja").render(
                method_name=method_name,
                method=method,
                path=path,
                path_params=path_params,
                path_params_snake_case=path_params_snake_case,
                schema=schema,
                operation_type=crud_type,
                status_code=response_info["status_code"],
                status_text=response_info["status_text"],
                headers=response_info["headers"],
                error_responses=error_responses,
                use_daos=self.config.use_daos,
            )
            handler_methods.append(method_code)
        return handler_methods

    def _generate_handler_code(
        self,
        persistent_schemas: list[str],
        all_methods: str,
        path_params: tuple[set[str], dict[str, str]]
    ):
        schema_filenames = [camel_to_snake(schema) + "_dao" for schema in persistent_schemas]

        header = self.jinja_env.get_template("handler_header.jinja").render(
            author=self.config.public_id.author,
            skill_name=self.config.public_id.name,
            schemas=persistent_schemas,
            schema_filenames=schema_filenames,
            use_daos=self.config.use_daos
        )
        main_handler = self.jinja_env.get_template("main_handler.jinja").render(
            all_methods=all_methods,
            unexpected_message_handler=self.jinja_env.get_template("unexpected_message_handler.jinja").render(),
            path_params=path_params[0],
            path_mappings=path_params[1],
            use_daos=self.config.use_daos
        )
        return header + main_handler

    def _get_path_params(self, openapi_spec: OpenAPI) -> tuple[set[str], dict[str, str]]:
        path_params = set()
        path_mappings = {}

        for path, path_item in openapi_spec.paths.items():
            path_segments = path.split("/")
            path_without_params = []
            params_mapping = {}

            # Check if path has any parameters
            has_params = any(segment.startswith("{") and segment.endswith("}")
                            for segment in path_segments)

            if not has_params:
                continue  # Skip paths without parameters

            # We process path segments
            for segment in path_segments:
                if segment.startswith("{") and segment.endswith("}"):
                    path_without_params.append("")
                    param_name = segment[1:-1]
                    snake_case_param = camel_to_snake(param_name)
                    path_params.add(snake_case_param)
                    params_mapping[param_name] = snake_case_param
                else:
                    path_without_params.append(segment)

            normalized_path = "/".join(path_without_params)
            if normalized_path:
                path_mappings[normalized_path] = {
                    "original_path": path,
                    "params": params_mapping
                }

            # We process path item parameters
            if isinstance(path_item, Reference):
                try:
                    path_item = path_item.resolve(openapi_spec)
                except Exception as e:
                    self.logger.exception(f"Failed to resolve reference for path {path}: {e}")
                    continue

            for param in path_item.parameters or []:
                if param.param_in == "path":
                    snake_case_param = camel_to_snake(param.name)
                    path_params.add(snake_case_param)
                    if normalized_path:
                        path_mappings[normalized_path]["params"][param.name] = snake_case_param

            # # Also check URL path for parameters
            # path_segments = path.split("/")
            # for segment in path_segments:
            #     if segment.startswith("{") and segment.endswith("}"):
            #         param_name = segment[1:-1]  # Remove { and }
            #         snake_case_param = camel_to_snake(param_name)
            #         path_params.add(snake_case_param)
            #         path_params_mapping[param_name] = snake_case_param

        return path_params, path_mappings

    def generate_method_name(self, http_method: str, path: str) -> str:
        """Generate method name based on HTTP method and path."""
        method_name = f"handle_{http_method.lower()}"
        parts = [part for part in path.strip("/").split("/") if part]
        name_parts = []
        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                param_name = part.strip("{}")
                param_name = self.sanitize_identifier(param_name)
                name_parts.append(f"by_{param_name}")
            else:
                part_name = self.sanitize_identifier(part)
                name_parts.append(part_name)
        method_name += "_" + "_".join(name_parts)
        return method_name

    def save_handler(self) -> None:
        """Save handler to file."""
        write_to_file(Path("handlers.py"), self.handler_code, file_type=FileType.PYTHON)

    def update_skill_yaml(self, file) -> None:
        """Update the skill.yaml file."""
        skill_yaml = read_yaml_file(file)

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

    def confirm_action(self, message):
        """Prompt the user for confirmation before performing an action."""
        if self.config.auto_confirm:
            self.logger.info(f"Auto confirming: {message}")
            return True
        response = input(f"{message} (y/n): ").lower().strip()
        return response in {"y", "yes"}

    def create_exceptions(self) -> None:
        """Create the exceptions file."""
        exceptions_template = self.jinja_env.get_template("exceptions.jinja").render()
        write_to_file(Path("exceptions.py"), exceptions_template, file_type=FileType.PYTHON)

    def present_actions(self):
        """Present the scaffold summary."""
        actions = [
            f"Generating handler based on OpenAPI spec: {self.config.spec_file_path}",
            f"Saving handler to: skills/{self.config.output}/handlers.py",
            f"Updating skill.yaml in skills/{self.config.output}/",
            f"Moving and updating my_model.py to strategy.py in: skills/{self.config.output}/",
            f"Removing behaviours.py in: skills/{self.config.output}/",
            f"Creating dialogues.py in: skills/{self.config.output}/",
            f"Creating exceptions.py in: skills/{self.config.output}/",
            "Fingerprinting the skill",
            "Running 'aea install'",
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
        name = camel_to_snake(name)
        name = re.sub(r"[^0-9a-zA-Z_]", "_", name)
        if name and name[0].isdigit():
            name = "_" + name
        return name.lower()

    def identify_persistent_schemas(self, api_spec: OpenAPI) -> list[str]:
        """Identify the persistent schemas."""
        schemas = api_spec.components.schemas if api_spec.components else {}
        schema_usage = defaultdict(set)

        def process_schema(schema: Any, usage_type: str) -> None:
            try:
                self.logger.debug(f"Processing schema: {schema}, type: {type(schema)}")
                schema = parse_schema_like(schema)

                if isinstance(schema, Reference):
                    schema_name = schema.ref.split("/")[-1]
                    self.logger.debug(f"Found reference to {schema_name}")
                    schema_usage[schema_name].add(usage_type)
                    referenced_schema = schemas.get(schema_name)
                    if referenced_schema:
                        referenced_schema = parse_schema_like(referenced_schema)
                        self.logger.debug(f"Referenced schema: {referenced_schema}")
                        if referenced_schema.properties:
                            for prop in referenced_schema.properties.values():
                                process_schema(prop, f"nested_{usage_type}")
                elif isinstance(schema, Schema):
                    if schema.properties:
                        for prop in schema.properties.values():
                            process_schema(prop, usage_type)
                    if schema.items:
                        process_schema(schema.items, usage_type)
            except Exception as e:
                self.logger.warning(f"Error processing schema: {e}")
                return

        for path, path_item in api_spec.paths.items():
            if isinstance(path_item, Reference):
                try:
                    path_item = path_item.resolve(api_spec)
                except Exception as e:
                    self.logger.error(f"Failed to resolve reference for path {path}: {e}")
                    continue

            for method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']:
                operation: Optional[Operation] = getattr(path_item, method, None)
                if operation:
                    if operation.requestBody:
                        for content in operation.requestBody.content.values():
                            try:
                                schema = content.media_type_schema
                                process_schema(schema, "request")
                            except Exception as e:
                                self.logger.warning(f"Error processing request schema: {e}")
                                continue

                    for response in operation.responses.values():
                        if response.content:
                            for content in response.content.values():
                                try:
                                    schema = content.media_type_schema
                                    process_schema(schema, "response")
                                except Exception as e:
                                    self.logger.warning(f"Error processing response schema: {e}")
                                    continue

        return [
            schema for schema, usage in schema_usage.items()
            if "response" in usage or "nested_request" in usage
        ]

    def _extract_response_info(self, operation: Operation) -> dict[str, Any]:
        responses = operation.responses

        status_code = 200
        status_text = "OK"
        headers = {}

        for code, response in responses.items():
            if code in {"200", "201", "204"}:
                status_code = int(code)
                status_text = response.description or "OK"
                headers = response.headers if response.headers is not None else {}
                break

        return {
            "status_code": status_code,
            "status_text": status_text,
            "headers": headers,
        }

    def _extract_error_responses(self, operation: Operation) -> dict[str, Any]:
        responses = operation.responses
        error_responses = {}

        error_mapping = {
            "400": ("BadRequestError", "Bad Request"),
            "401": ("UnauthorizedError", "Unauthorized"),
            "403": ("ForbiddenError", "Forbidden"),
            "404": ("NotFoundError", "Not Found"),
            "422": ("ValidationError", "Unprocessable Entity"),
        }

        for code, response in responses.items():
            if code in {"400", "401", "403", "404", "422"}:
                error_info = error_mapping.get(code, ("Exception", response.description or "Error"))
                error_responses[code] = {
                    "exception": error_info[0],
                    "message": response.description or error_info[1],
                    "status_text": error_info[1],
                }

        return error_responses


class HandlerScaffoldBuilder:
    """Builder for HandlerScaffolder."""

    def __init__(self):
        """Initialize HandlerScaffoldBuilder."""
        self.config: Optional[ScaffolderConfig] = None
        self.logger = None

    def create_scaffolder(
        self,
        spec_file_path: str,
        public_id: PublicId,
        logger,
        verbose: bool = True,
        new_skill: bool = False,
        auto_confirm: bool = False,
        use_daos: bool = False,
    ):
        """Initialize HandlerScaffoldBuilder."""
        try:
            self.config = ScaffolderConfig(
                spec_file_path=spec_file_path,
                public_id=public_id,
                verbose=verbose,
                new_skill=new_skill,
                auto_confirm=auto_confirm,
                use_daos=use_daos,
            )
        except ValidationError as e:
            logger.exception(f"Configuration validation error: {e}")
            msg = f"Failed to initialize ScaffolderConfig: {e}"
            raise ScaffolderError(msg) from e
        self.logger = logger
        return self

    def build(self) -> HandlerScaffolder:
        """Build the scaffolder."""
        if not self.config:
            msg = "Scaffolder not initialized. Call create_scaffolder first."
            self.logger.error(msg)
            raise ScaffolderError(msg)
        return HandlerScaffolder(self.config, self.logger)

# HELPER FUNCTIONS


def load_openapi_spec(spec_file_path: str, logger) -> OpenAPI:
    """Load the OpenAPI spec."""
    try:
        openapi_spec_dict = read_yaml_file(spec_file_path)
        return OpenAPI(**openapi_spec_dict)
    except FileNotFoundError as e:
        msg = f"OpenAPI specification file not found: {spec_file_path}"
        logger.exception(msg)
        raise ScaffolderError(msg) from e
    except ValidationError as e:
        msg = f"OpenAPI specification validation error: {e}"
        logger.exception(msg)
        raise ScaffolderError(msg) from e


def get_crud_classification(openapi_spec: OpenAPI, logger) -> list[dict]:
    """Get the CRUD classification."""
    classifications = []
    for path, path_item in openapi_spec.paths.items():
        if isinstance(path_item, Reference):
            try:
                path_item = path_item.resolve(openapi_spec)
            except Exception as e:
                msg = f"Failed to resolve reference for path {path}: {e}"
                logger.exception(msg)
                continue

        for method in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]:
            operation: Optional[Operation] = getattr(path_item, method.lower(), None)
            if operation:
                if method in {"patch", "options", "head", "trace"}:
                    msg = f"Method {method.upper()} is not currently supported"
                    raise ScaffolderError(msg)

                crud_type = classify_post_operation(operation, path, logger) if method == "post" else "read"
                classifications.append({
                    "path": path,
                    "method": method,
                    "operationId": operation.operationId,
                    "crud_type": crud_type,
                })
    logger.info(f"Classifications: {classifications}")
    return classifications


def classify_post_operation(operation: Operation, path: str, logger) -> str:
    """Classify a POST operation as CRUD or other based on heuristics."""
    keywords = (
        (operation.operationId or "") + " " +
        (operation.summary or "") + " " +
        (operation.description or "")
    ).lower()

    # Define keyword sets for each CRUD operation
    create_keywords = {"create", "new", "add", "post"}
    read_keywords = {"read", "get", "fetch", "retrieve", "list"}
    update_keywords = {"update", "modify", "change", "edit", "patch"}
    delete_keywords = {"delete", "remove", "del"}

    # Define regex to detect path parameters
    has_path_param = bool(re.search(r"/\{[^}]+\}", path))

    # Keyword-based classification
    if any(word in keywords for word in create_keywords):
        return CrudOperation.CREATE
    elif any(word in keywords for word in read_keywords):
        return CrudOperation.READ
    elif any(word in keywords for word in update_keywords):
        return CrudOperation.UPDATE
    elif any(word in keywords for word in delete_keywords):
        return CrudOperation.DELETE

    # Heuristic based on presence of path parameters and response codes
    if has_path_param:
        # Analyze response status codes
        success_responses = {code: resp for code, resp in operation.responses.items() if code in {"200", "201", "204"}}
        if "201" in success_responses:
            return CrudOperation.CREATE
        elif "204" in success_responses:
            # 204 No Content is often used for Delete operations
            return CrudOperation.DELETE
        elif "200" in success_responses:
            # 200 OK could indicate Read or Update; prefer Update if path has parameters
            return CrudOperation.UPDATE

    # Default to OTHER if no heuristics match
    logger.warning(f"Could not classify POST operation '{operation.operationId}' at path '{path}'.")
    return CrudOperation.OTHER


def parse_schema_like(data: Union[dict, Reference, Schema]) -> Union[Schema, Reference]:
    """Parse a schema-like object into a Schema or Reference."""
    if isinstance(data, (Schema, Reference)):
        return data
    if isinstance(data, dict):
        if "$ref" in data:
            return Reference(**data)
        return Schema(**data)
    return data

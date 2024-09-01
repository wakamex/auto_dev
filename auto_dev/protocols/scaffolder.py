"""Protocol scaffolder."""

import re
import ast
import datetime
import tempfile
import textwrap
import subprocess
from pathlib import Path
from itertools import starmap
from collections import namedtuple

import yaml
from aea.protocols.generator.base import ProtocolGenerator

from auto_dev.fmt import Formatter
from auto_dev.utils import currenttz, get_logger, remove_prefix, camel_to_snake
from auto_dev.constants import DEFAULT_TZ, DEFAULT_ENCODING
from auto_dev.data.connections.template import HEADER


ProtocolSpecification = namedtuple("ProtocolSpecification", ["metadata", "custom_types", "speech_acts"])


README_TEMPLATE = """
# {name} Protocol

## Description

...

## Specification

```yaml
{protocol_definition}
```
"""


def read_protocol(filepath: str) -> ProtocolSpecification:
    """Read protocol specification."""
    content = Path(filepath).read_text(encoding=DEFAULT_ENCODING)
    if "```" in content:
        if content.count("```") != 2:
            msg = "Expecting a single code block"
            raise ValueError(msg)
        content = remove_prefix(content.split("```")[1], "yaml")

    # use ProtocolGenerator to validate the specification

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
        Path(temp_file.name).write_text(content, encoding=DEFAULT_ENCODING)
        ProtocolGenerator(temp_file.name)

    metadata, custom_types, speech_acts = yaml.safe_load_all(content)

    return ProtocolSpecification(metadata, custom_types, speech_acts)


def parse_enums(protocol: ProtocolSpecification) -> dict[str, dict[str, str]]:
    """Parse enums."""
    enums = {}
    for ct_name, definition in protocol.custom_types.items():
        if not definition.startswith("enum "):
            continue
        result = re.search(r"\{([^}]*)\}", definition)
        if not result:
            msg = f"Error parsing enum fields from: {definition}"
            raise ValueError(msg)
        fields = {}
        for enum in filter(None, result.group(1).strip().split(";")):
            name, number = enum.split("=")
            fields[name.strip()] = number.strip()
        enums[ct_name[3:]] = fields
    return enums


def get_docstring_index(node: ast.stmt):
    """Get docstring index."""

    def is_docstring(stmt: ast.stmt):
        return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str)

    return next((i + 1 for i, stmt in enumerate(node.body) if is_docstring(stmt)), 0)


def get_raise_statement(stmt) -> ast.stmt:
    """Get raise statement."""
    return next(
        statement
        for statement in stmt.body
        if isinstance(statement, ast.Raise)
        and isinstance(statement.exc, ast.Name)
        and statement.exc.id == "NotImplementedError"
    )


class EnumModifier:
    """EnumModifier."""

    def __init__(self, protocol_path: Path, logger):
        """Initialize EnumModifier."""
        self.protocol_path = protocol_path
        self.protocol = read_protocol(protocol_path / "README.md")
        self.logger = logger

    def augment_enums(self) -> None:
        """Agument enums."""
        enums = parse_enums(self.protocol)
        if not enums:
            return

        custom_types_path = self.protocol_path / "custom_types.py"
        content = custom_types_path.read_text()
        root = ast.parse(content)

        new_import = ast.ImportFrom(module="enum", names=[ast.alias(name="Enum", asname=None)], level=0)
        root.body.insert(get_docstring_index(root), new_import)

        for node in root.body:
            if isinstance(node, ast.ClassDef) and node.name in enums:
                self._process_enum(node, enums)

        modified_code = ast.unparse(root)
        updated_content = self._update_content(content, modified_code)
        self._format_and_write_to_file(custom_types_path, updated_content)
        self.logger.info(f"Updated: {custom_types_path}")

    def _update_content(self, content: str, modified_code: str):
        i = content.find(modified_code.split("\n")[0])
        return content[:i] + modified_code

    def _format_and_write_to_file(self, file_path: Path, content: str) -> None:
        file_path.write_text(content)
        Formatter(verbose=False, remote=False).format(file_path)

    def _process_enum(self, node: ast.ClassDef, enums) -> None:
        camel_to_snake(node.name)
        node.bases = [ast.Name(id="Enum", ctx=ast.Load())]

        class_attrs = self._create_class_attributes(enums[node.name], node)
        docstring_index = get_docstring_index(node)
        node.body = node.body[:docstring_index] + class_attrs + node.body[docstring_index:]
        self._update_methods(node)

    def _create_class_attributes(self, enum_values: dict[str, str], node: ast.ClassDef):
        def to_ast_assign(attr_name: str, attr_value: str):
            return ast.Assign(
                targets=[ast.Name(id=attr_name, ctx=ast.Store())],
                value=ast.Constant(value=int(attr_value)),
                lineno=node.lineno,
            )

        return list(starmap(to_ast_assign, enum_values.items()))

    def _update_methods(self, node: ast.ClassDef) -> None:
        to_remove = []
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.FunctionDef):
                if stmt.name in {"__init__", "__eq__"}:
                    to_remove.append(i)
                elif stmt.name == "encode":
                    self._modify_encode_function(stmt, node)
                elif stmt.name == "decode":
                    self._modify_decode_function(stmt, node)

        for i in sorted(to_remove, reverse=True):
            node.body.pop(i)

    def _modify_encode_function(self, stmt: ast.stmt, node: ast.ClassDef) -> None:
        name = camel_to_snake(node.name)
        statement = get_raise_statement(stmt)
        j = stmt.body.index(statement)
        stmt.body[j] = ast.Expr(
            value=ast.Assign(
                targets=[
                    ast.Attribute(
                        value=ast.Name(id=f"{name}_protobuf_object", ctx=ast.Load()), attr=name, ctx=ast.Store()
                    )
                ],
                value=ast.Attribute(value=ast.Name(id=f"{name}_object", ctx=ast.Load()), attr="value", ctx=ast.Load()),
                lineno=statement.lineno,
            )
        )

    def _modify_decode_function(self, stmt: ast.stmt, node: ast.ClassDef) -> None:
        name = camel_to_snake(node.name)
        statement = get_raise_statement(stmt)
        j = stmt.body.index(statement)
        stmt.body[j] = ast.Return(
            value=ast.Call(
                func=ast.Name(id=node.name, ctx=ast.Load()),
                args=[
                    ast.Attribute(
                        value=ast.Name(id=f"{name}_protobuf_object", ctx=ast.Load()), attr=name, ctx=ast.Load()
                    )
                ],
                keywords=[],
            )
        )


class CommentSplitter(ast.NodeVisitor):
    """CommentSplitter for parsing AST."""

    def __init__(self, max_line_length=120):
        self.max_line_length = max_line_length
        self.result = []

    def split_docstring(self, docstring):
        """Split docstring."""
        split_lines = []
        for line in docstring.splitlines():
            if len(line) > self.max_line_length:
                indentation = len(line) - len(line.lstrip())
                wrapped_lines = textwrap.wrap(line, width=self.max_line_length, subsequent_indent=" " * indentation)
                split_lines.extend(wrapped_lines)
            else:
                split_lines.append(line)
        return "\n".join(split_lines)

    def visit_FunctionDef(self, node):  # noqa
        """process the function's docstring"""
        if ast.get_docstring(node):
            original_docstring = ast.get_docstring(node, clean=False)
            split_docstring = self.split_docstring(original_docstring)
            node.body[0].value = ast.Str(s=split_docstring)

        # Continue visiting the rest of the function
        self.generic_visit(node)

    def visit_Module(self, node):  # noqa
        """Process the module-level docstring"""
        if ast.get_docstring(node):
            original_docstring = ast.get_docstring(node, clean=False)
            split_docstring = self.split_docstring(original_docstring)
            node.body[0].value = ast.Str(s=split_docstring)

        # Continue visiting the rest of the module
        self.generic_visit(node)


def split_long_comment_lines(code: str, max_line_length: int = 120) -> str:
    """Split long comment lines given a code string."""
    tree = ast.parse(code)
    splitter = CommentSplitter(max_line_length=max_line_length)
    splitter.visit(tree)
    return ast.unparse(tree)


class ProtocolScaffolder:
    """ProtocolScaffolder."""

    def __init__(self, protocol_specification_path: str, language, logger, verbose: bool = True):
        """Initialize ProtocolScaffolder."""
        self.logger = logger or get_logger()
        self.verbose = verbose
        self.language = language
        self.protocol_specification_path = protocol_specification_path
        self.logger.info(f"Read protocol specification: {protocol_specification_path}")

    def generate(self) -> None:
        """Generate protocol."""
        command = f"aea generate protocol {self.protocol_specification_path} --l {self.language}"
        result = subprocess.run(command, shell=True, capture_output=True, check=False)
        if result.returncode != 0:
            msg = f"Protocol scaffolding failed: {result.stderr}"
            raise ValueError(msg)

        protocol = read_protocol(self.protocol_specification_path)
        protocol_author = protocol.metadata["author"]
        protocol_name = protocol.metadata["name"]
        protocol_version = protocol.metadata["version"]

        protocol_path = Path.cwd() / "protocols" / protocol_name

        readme = protocol_path / "README.md"
        protocol_definition = Path(self.protocol_specification_path).read_text(encoding=DEFAULT_ENCODING)
        kwargs = {
            "name": " ".join(map(str.capitalize, protocol_name.split("_"))),
            "protocol_definition": protocol_definition,
        }
        content = README_TEMPLATE.format(**kwargs)
        readme.write_text(content.strip(), encoding=DEFAULT_ENCODING)

        EnumModifier(protocol_path, self.logger).augment_enums()

        self.cleanup_protocol(protocol_path, protocol_author, protocol_definition, protocol_name)

        command = f"aea fingerprint protocol {protocol_author}/{protocol_name}:{protocol_version}"
        result = subprocess.run(command, shell=True, capture_output=True, check=False)
        if result.returncode != 0:
            msg = f"Protocol fingerprinting failed: {result.stderr}"
            raise ValueError(msg)

        protocol_path = Path.cwd() / "protocols" / protocol_name

        self.logger.info(f"New protocol scaffolded at {protocol_path}")

    def cleanup_protocol(self, protocol_path, protocol_author, protocol_definition, protocol_name) -> None:
        """Cleanup protocol."""
        # We add in some files. that are necessary for the protocol to pass linting...
        test_init = protocol_path / "tests" / "__init__.py"
        test_init.touch()

        # We template in the necessary copywrite information
        test_init.write_text(
            HEADER.format(
                author=protocol_author,
                year=datetime.datetime.now(tz=currenttz()).year,
            ),
            encoding=DEFAULT_ENCODING,
        )
        # We make a protocol_spec.yaml file
        protocol_spec = protocol_path / "protocol_spec.yaml"
        protocol_spec.write_text(protocol_definition, encoding=DEFAULT_ENCODING)

        # We remove from the following lines from the *_pb2.py file
        regexs = [
            "_runtime_version",
        ]
        pb2_file = protocol_path / f"{protocol_name}_pb2.py"
        content = pb2_file.read_text(encoding=DEFAULT_ENCODING)
        new_content = ""
        for line in content.splitlines():
            for regex in regexs:
                if regex in line:
                    break
            else:
                new_content += line + "\n"
        pb2_file.write_text(new_content, encoding=DEFAULT_ENCODING)

        # We split long lines in the protocol_spec.yaml file
        custom_types = protocol_path / "custom_types.py"
        content = custom_types.read_text(encoding=DEFAULT_ENCODING)
        updated_content = split_long_comment_lines(content)
        custom_types.write_text(updated_content, encoding=DEFAULT_ENCODING)

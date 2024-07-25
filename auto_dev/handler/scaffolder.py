"""Handler scaffolder."""

import os
import yaml
from pathlib import Path


HANDLER_HEADER_TEMPLATE = """
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 {author}
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"This package contains a scaffold of a handler."

from typing import Optional, cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.{author}.protocols.http.message import HttpMessage
from packages.{author}.skills.{skill_name}.dialogues import HttpDialogue
from packages.{author}.skills.{skill_name}.strategy import Strategy

class HttpHandler(Handler):
    \"\"\"Implements the HTTP handler.\"\"\"

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[str]

    def setup(self) -> None:
        \"\"\"Set up the handler.\"\"\"
        self.strategy = cast(Strategy, self.context.strategy)

    def handle_get(self, route, id=None):
        \"\"\"handle get protocol\"\"\"
        raise NotImplementedError

    def handle_post(self, route, id, body):
        \"\"\"handle post protocol\"\"\"
        raise NotImplementedError

    def teardown(self) -> None:
        \"\"\"Tear down the handler.\"\"\"
        pass

"""

HANDLER_METHOD_TEMPLATE = """
    def handle(self, message):
        "main handler method"
        url = message.url
        parts = url.split('/')
        if len(parts) == 3:
            route = parts[-2]
            id = parts[-1]
            body = json.loads(message.body.decode("utf-8"))
            return self.handle_post(route, id, body)
        elif len(parts) == 2:
            route = parts[1]
            return self.handle_get(route)
        return self.handle_unexpected_message(message)
        {unexpected_message_handler}
"""

PATH_FILTER_TEMPLATE = """
        if filter == "{path}":
            return self.{method_filters}{route}(message)
"""

UNEXPECTED_MESSAGE_HANDLER_TEMPLATE = """
    def handle_unexpected_message(self, message):
        \"\"\"handler for unexpected messages\"\"\"
        self.context.logger.info("received unexpected message: {}".format(message))
        raise NotImplementedError
"""

DIALOGUES_CODE = """
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

# we do a backslash here like so:
\"\"\"
This module contains the classes required for dialogue management.

- DefaultDialogue: The dialogue class maintains state of a dialogue of type default and manages it.
- DefaultDialogues: The dialogues class keeps track of all dialogues of type default.
- HttpDialogue: The dialogue class maintains state of a dialogue of type http and manages it.
- HttpDialogues: The dialogues class keeps track of all dialogues of type http.


\"\"\"

from typing import Any

from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.skills.base import Model

from packages.eightballer.protocols.http.dialogues import (
    HttpDialogue as BaseHttpDialogue,
)
from packages.eightballer.protocols.http.dialogues import (
    HttpDialogues as BaseHttpDialogues,
)

HttpDialogue = BaseHttpDialogue


class HttpDialogues(Model, BaseHttpDialogues):
    \"\"\"The dialogues class keeps track of all dialogues.\"\"\"

    def __init__(self, **kwargs: Any) -> None:
        \"\"\"Initialize the Dialogues class.\"\"\"
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            \"\"\"
            Infer the role of the agent from an incoming/outgoing first message.

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            \"\"\"
            del message, receiver_address
            return BaseHttpDialogue.Role.SERVER

        BaseHttpDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )

"""


def load_spec_file(spec_file: str):
    """
    Reads the specified YAML file and returns its contents as a dictionary.

    :param spec_file: The path to the YAML file to read.
    :return: The contents of the YAML file as a dictionary.
    """
    with open(spec_file, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing YAML: {exc}")


def save_file(path: Path, content: str) -> None:
    """
    Writes the given content to the specified file.

    :param path: The path to the file to write to.
    :param content: The content to write to the file.
    """
    print(path)
    with open(path, "w") as f:
        try:
            f.write(content)
        except Exception as e:
            raise ValueError(f"Error writing to file: {e}")


def prompt_user(message: str) -> bool:
    """
    Prompts the user for a yes or no response.

    :param message: The message to display to the user.
    :return: True if user responds with 'y' or 'yes', False otherwise.
    """
    valid_responses = {"y", "yes", "n", "no"}
    while True:
        response: str = input(f"{message} (y/n): ").lower().strip()
        if response in valid_responses:
            return response in {"y", "yes"}
        print("Invalid response. Please enter 'y' or 'n'.")


def generate_handler_code(spec, author: str) -> str:
    """
    Generate the handler code based on the OpenAPI spec
    """
    paths = spec["paths"]
    handler_methods = []

    for path, path_spec in paths.items():
        for method, operation in path_spec.items():
            method_name: str = f"handle_{method.lower()}_{path.lstrip('/').replace('/', '_').replace('{', '').replace('}', '')}"
            params: List[str] = []
            if "{" in path:
                params.append("id")
            if method.lower() in ["post", "put", "patch"]:
                params.append("body")

            param_str: str = ", ".join(["self"] + params)

            method_code: str = f"""
    def {method_name}({param_str}):
        \"\"\"
        Handle {method.upper()} request for {path}
        \"\"\"
        # TODO: Implement {method.upper()} logic for {path}
        raise NotImplementedError
"""
            handler_methods.append(method_code)

    all_methods: str = "\n".join(handler_methods)

    handler_code: str = HANDLER_HEADER_TEMPLATE.format(
        author=author, skill_name=spec["info"]["title"].replace(" ", "_")
    )

    main_handler: str = f"""
    def handle(self, message: HttpMessage) -> None:
        \"\"\"Handle incoming HTTP messages\"\"\"
        method = message.method
        url = message.url
        body = message.body

        path_parts = url.split('/')
        path = '/' + '/'.join(path_parts[1:])
        
        if '{{' in path:
            id_index = path_parts.index([part for part in path_parts if '{{' in part][0])
            id = path_parts[id_index]
            path = '/' + '/'.join(path_parts[1:id_index] + ['{{'+ path_parts[id_index][1:-1] + '}}'] + path_parts[id_index+1:])
        
        handler_method = getattr(self, f"handle_{{method.lower()}}_{{path.lstrip('/').replace('/', '_').replace('{', '').replace('}', '')}}", None)
        
        if handler_method:
            kwargs = {{'body': body}} if method.lower() in ['post', 'put', 'patch'] else {{}}
            if '{{' in path:
                kwargs['id'] = id
            return handler_method(**kwargs)
        
        return self.handle_unexpected_message(message)
    
{all_methods}

{UNEXPECTED_MESSAGE_HANDLER_TEMPLATE}
"""

    handler_code += main_handler
    return handler_code


def update_skill_yaml(skill_yaml_file):
    """
    Update the skill.yaml file
    """

    with open(skill_yaml_file, "r") as f:
        skill_yaml = yaml.safe_load(f)

    print(skill_yaml)
    skill_yaml["protocols"] = [
        "eightballer/http:0.1.0:bafybeia2yjjpa57ihbfru54lvq3rru5vtaomyor3fn4zz4ziiaum5yywje",
    ]
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

    with open(skill_yaml_file, "w") as f:
        yaml.safe_dump(skill_yaml, f, sort_keys=False)


def move_and_update_my_model(spec) -> None:
    """
    Reads in the my_model.py file and updates it.
    We replace the name MyModel with the name Strategy.
    """

    with open("my_model.py", "r") as f:
        strategy_code: str = f.read()
    strategy_code = strategy_code.replace("MyModel", "Strategy")

    # we now remove the my_model.py file
    os.remove("my_model.py")
    # we now create the strategy.py file
    strategy_file = "strategy.py"
    with open(strategy_file, "w") as f:
        f.write(strategy_code)


def remove_behaviours() -> None:
    """
    Remove the behaviours
    """
    os.remove("behaviours.py")


def create_dialogues(spec) -> None:
    """
    Create the dialogues
    """
    dialogues_file = "dialogues.py"
    with open(dialogues_file, "w") as f:
        f.write(DIALOGUES_CODE)

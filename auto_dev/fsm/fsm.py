"""
Tools to parse fsm specs.
"""
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Dict, List, Tuple

import yaml

from auto_dev.constants import DEFAULT_ENCODING

# we define our base template
BASE_MERMAID_TEMPLATE = Template(
    """
graph TD
  $start_state
  $states
  $transitions
"""
)

# we define the FSM template

SAMPLE_MERMAID = """
graph TD
    A[Christmas] -->|Get money| B(Go shopping)
    B --> C{Let me think}
    C -->|One| D[Laptop]
    C -->|Two| E[iPhone]
    C -->|Three| F[fa:fa-car Car]
"""

STATE_TEMPLATE = Template("""$state""")
TRANSITION_TEMPLATE = Template("""$start_state -->|$transition| $end_state""")


@dataclass
class FsmSpec:
    """
    We represent a fsm spec.
    """

    alphabet_in: List[str]
    default_start_state: str
    final_states: List[str]
    label: str
    start_states: List[str]
    states: List[str]
    transition_func: Dict[Tuple[str, str], str]

    @classmethod
    def from_yaml(cls, yaml_str: str):
        """
        We create a FsmSpec from a yaml string.
        """
        fsm_spec = yaml.safe_load(yaml_str)
        return cls(**fsm_spec)

    @classmethod
    def from_path(cls, path: Path):
        """
        We create a FsmSpec from a yaml file.
        """
        with open(path, "r", encoding=DEFAULT_ENCODING) as file_pointer:
            return cls.from_yaml(file_pointer.read())

    def to_mermaid(self):
        """
        We convert the FsmSpec to a mermaid string.
        """
        start_state = STATE_TEMPLATE.substitute(state=self.default_start_state)
        # join on new line
        states = "\n  ".join([STATE_TEMPLATE.substitute(state=state) for state in self.states])
        transitions = []
        for transition, end_state in self.transition_func.items():
            _start_state, _transition = transition[1:-1].split(", ")
            transitions.append(
                TRANSITION_TEMPLATE.substitute(start_state=_start_state, transition=_transition, end_state=end_state)
            )
        # we join on new line
        transitions = "\n  ".join(transitions)

        return BASE_MERMAID_TEMPLATE.substitute(start_state=start_state, states=states, transitions=transitions)

    @classmethod
    def from_mermaid(cls, mermaid_str: str):
        """
        Parse a mermaid string to a FsmSpec.
        note, we need to create a graph like structure.
        we parse each line and create a node and a edge.
        """

        states = []
        transitions = []

        for line in mermaid_str.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("graph"):
                continue
            if line.startswith("%%"):
                continue
            items = line.split()
            if len(items) == 1:
                states.append(items[0])
            else:
                start_state, _transition, end_state = items
                transition = _transition.split("|")[1]
                transitions.append(((start_state, transition), end_state))
        # we need to create the alphabet_in
        alphabet_in = sorted(list(set([transition[1] for transition, _ in transitions])))  # pylint: disable=R1718
        # we need to create the transition_func
        transition_func = {}
        for transition, end_state in transitions:
            key = f"({transition[0]}, {transition[1]})"
            transition_func[key] = end_state
        # we need to create the start_states
        # we can do this by using our transition_func to find the start states
        initial_state = states.pop(0)

        return cls(
            alphabet_in=alphabet_in,
            default_start_state=initial_state,
            final_states=[],
            label="HelloWorldAbciApp",
            start_states=[initial_state],
            states=states,
            transition_func=transition_func,
        )

    def to_string(self):
        """
        We convert the FsmSpec to a string.
        """
        return str(yaml.dump(self.__dict__))

import random
from typing import Any


def generate_dummy_data(models: dict[str, Any], num_instances: int = 5) -> dict[str, list[dict[str, Any]]]:
    """Generate dummy data for the given models."""
    dummy_data = {}
    for model_name, model_schema in models.items():
        dummy_data[model_name] = [_generate_model_dummy_data(model_schema) for _ in range(num_instances)]
    return dummy_data


def _generate_model_dummy_data(model_schema: dict[str, Any]) -> dict[str, Any]:
    properties = model_schema.get("properties", {})
    dummy_instance = {}
    for prop_name, prop_schema in properties.items():
        dummy_instance[prop_name] = _generate_property_dummy_data(prop_schema)
    return dummy_instance


def _generate_property_dummy_data(prop_schema: dict[str, Any]) -> Any:
    prop_type = prop_schema.get("type", "string")

    type_generators = {
        "string": lambda: f"dummy_{random.randint(1000, 9999)}",  # noqa: S311
        "integer": lambda: random.randint(1, 100),  # noqa: S311
        "number": lambda: round(random.uniform(1, 100), 2),  # noqa: S311
        "boolean": lambda: random.choice([True, False]),  # noqa: S311
        "array": lambda: [_generate_property_dummy_data(prop_schema.get("items", {})) for _ in range(3)],
        "object": lambda: _generate_model_dummy_data(prop_schema),
    }

    return type_generators.get(prop_type, lambda: None)()


def generate_single_dummy_data(model_schema: dict[str, Any]) -> dict[str, Any]:
    """Generate a single instance of dummy data for the given model schema."""
    return _generate_model_dummy_data(model_schema)

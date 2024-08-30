from typing import Any

from jinja2 import Environment, FileSystemLoader

from auto_dev.constants import JINJA_DAO_FOLDER


class DAOGenerator:
    """DAO generator class."""
    def __init__(self, models: dict[str, Any], paths: dict[str, Any]):
        self.models = models
        self.paths = paths
        self.env = Environment(loader=FileSystemLoader(JINJA_DAO_FOLDER))
        self.template = self.env.get_template("dao_template.jinja")

    def generate_dao_classes(self) -> dict[str, str]:
        """Generate DAO classes."""
        dao_classes = {}
        for model_name, model_schema in self.models.items():
            dao_classes[f"{model_name}DAO"] = self._generate_dao_class(model_name, model_schema)
        return dao_classes

    def _generate_dao_class(self, model_name: str, model_schema: dict[str, Any]) -> str:
        other_model_names = [name for name in self.models.keys() if name != model_name]
        properties = model_schema.get("properties", {})
        return self.template.render(
            model_name=model_name,
            model_schema=model_schema,
            other_model_names=other_model_names,
            properties=properties
        )

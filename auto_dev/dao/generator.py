from typing import Any, Dict


class DAOGenerator:
    """DAO generator class."""
    def __init__(self, models: Dict[str, Any], paths: Dict[str, Any]):
        self.models = models
        self.paths = paths

    def generate_dao_classes(self) -> Dict[str, str]:
        """Generate DAO classes."""
        dao_classes = {}
        for model_name, model_schema in self.models.items():
            dao_classes[f"{model_name}DAO"] = self._generate_dao_class(model_name, model_schema)
        return dao_classes

    def _generate_dao_class(self, model_name: str, model_schema: Dict[str, Any]) -> str:
        properties = model_schema.get("properties", {})
        class_code = f"from pathlib import Path\n\n\n"
        class_code += f"class {model_name}DAO:\n"
        class_code += f"    def __init__(self):\n"
        class_code += f"        self.file_name = Path(__file__).parent / '{model_name.lower()}.json'\n"
        class_code += f"        self.data = self._load_data()\n\n"
        class_code += f"    def _load_data(self):\n"
        class_code += f"        import json\n"
        class_code += f"        try:\n"
        class_code += f"            with open(self.file_name, 'r') as f:\n"
        class_code += f"                return json.load(f)\n"
        class_code += f"        except FileNotFoundError:\n"
        class_code += f"            return []\n\n"
        class_code += f"    def _save_data(self):\n"
        class_code += f"        import json\n"
        class_code += f"        with open(self.file_name, 'w') as f:\n"
        class_code += f"            json.dump(self.data, f, indent=2)\n\n"
        class_code += self._generate_crud_methods()
        return class_code

    def _generate_crud_methods(self) -> str:
        methods = ""
        methods += self._generate_insert_method()
        methods += self._generate_read_methods()
        methods += self._generate_update_method()
        methods += self._generate_delete_method()
        return methods

    def _generate_insert_method(self) -> str:
        method = "    def insert(self, **kwargs):\n"
        method += "        self.data.append(kwargs)\n"
        method += "        self._save_data()\n\n"
        return method

    def _generate_read_methods(self) -> str:
        methods = "    def get_all(self):\n"
        methods += "        return self._load_data()\n\n"

        methods += "    def get_by_id(self, id: int):\n"
        methods += "        data = self._load_data()\n"
        methods += "        for item in data:\n"
        methods += "            if item.get('id') == id:\n"
        methods += "                return item\n"
        methods += "        return None\n\n"
        return methods

    def _generate_update_method(self) -> str:
        method = "    def update(self, id: int, **kwargs):\n"
        method += "        data = self._load_data()\n"
        method += "        for item in data:\n"
        method += "            if item.get('id') == id:\n"
        method += "                item.update(kwargs)\n"
        method += "                return item\n"
        method += "        return None\n\n"
        return method

    def _generate_delete_method(self) -> str:
        method = "    def delete(self, id: int):\n"
        method += "        data = self._load_data()\n"
        method += "        self.data = [item for item in data if item.get('id') != id]\n"
        method += "        self._save_data()\n\n"
        return method

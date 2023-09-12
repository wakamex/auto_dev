"""
Contains the template for the README.md file
"""

DIR = "./"

TEMPLATE = """# {project_name}
{description}

## Installation
```bash
pip install {project_name}
```

## Usage
```python
import {project_name}
```

## Contributing

### Setup
```bash
git clone https://github.com/{author}/{project_name}
cd {project_name}
poetry install
```

### Testing
```bash
make test
```

### Linting
```bash
make lint
```

### Formatting
```bash
make fmt
```

### Releasing
```bash
make release
```

## License
This project is licensed under the terms of the MIT license.
"""


REQUIRED_KEYS = [
    "project_name",
    "description",
]


EXTENSION = ".md"

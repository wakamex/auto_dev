"""
Contains the template for the README.md file
"""

TEMPLATE = """# {repo_name}
{repo_description}

## Installation
```bash
pip install {repo_name}
```

## Usage
```python
import {repo_name}
```

## Contributing

### Setup
```bash
git clone {repo_url}
cd {repo_name}
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


EXTENSION = ".md"

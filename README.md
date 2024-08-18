# micro-registry

**micro-registry** is a Python library for managing and loading class instances from modules and YAML configurations. It allows dynamic registration of classes and instantiation of objects, making it ideal for plugin-based architectures.

## Features

- **Dynamic Class Registration**: Register classes from modules dynamically.
- **Instance Management**: Create and manage instances of registered classes.
- **YAML Configuration**: Load instances and their configurations from YAML files.

## Installation

You can install the package via pip:

```bash
pip install micro-registry
```

Or clone the repository and install it locally:

```bash
git clone https://github.com/yourusername/micro-registry.git
cd micro-registry
pip install .
```

## Usage

### Registering Classes

You can register a class using the `@register_class` decorator:

```python
from micro_registry.registry import register_class

@register_class
class MyClass:
    def __init__(self, param1):
        self.param1 = param1
```

### Creating Instances

Once registered, you can create instances of these classes:

```python
from micro_registry.registry import create_instance

instance = create_instance('MyClass', param1='value1')
print(instance.param1)  # Outputs: value1
```

### Loading Instances from YAML

You can also load instances from a YAML configuration file:

```python
from micro_registry.registry import load_instances_from_yaml

load_instances_from_yaml('instances.yaml')
instance = instance_registry['MyInstance']
print(instance.param1)  # Outputs: value1
```

### Development

To contribute, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/yourusername/micro_registry.git
```

2. Install the development dependencies:

```bash
pip install -e .[dev]
```

3. Run tests:

```bash
pytest
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or contributions, reach out at your.email@example.com.
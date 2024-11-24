# import micro-registry

**micro-registry** is a Python library that provides a flexible and dynamic way to manage classes and their instances. It simplifies the development of complex systems by introducing mechanisms for dynamic class registration, instance creation, and configuration loading from YAML files. The library also implements the **MicroComponent** pattern and provides built-in RESTful APIs for component management.

## Features

- **Dynamic Class Registration**: Easily register classes using decorators for dynamic instantiation.
- **MicroComponent Pattern**: Build hierarchical component systems with parent-child relationships.
- **Instance Management**: Create and manage instances of registered classes with ease.
- **YAML Configuration Loading**: Define your system components in YAML files for flexible configuration.
- **Use regular Modules**: Register instances of class from regular python packages.
- **Built-in RESTful APIs**: Use the `RegistryAPI` and `ComponentAPI` to interact with your components over HTTP.
- **Plugin Architecture Support**: Load modules dynamically to extend functionality without modifying the core system.

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

## Getting Started

### Registering Classes

Registering classes is straightforward using the `@register_class` decorator. This allows the class to be dynamically instantiated later.

```python
from micro_registry.registry import register_class

@register_class
class MyComponent:
    def __init__(self, name, **kwargs):
        self.name = name
        # Additional initialization

    def start(self):
        print(f"Component {self.name} started.")

    def stop(self):
        print(f"Component {self.name} stopped.")
```

### The MicroComponent Pattern

The **MicroComponent** pattern provides a base class for creating components with hierarchical relationships. Components can have parents and children, making it easy to build complex systems.

```python
from micro_registry.component import MicroComponent

@register_class
class MyMicroComponent(MicroComponent):
    def __init__(self, name, parent=None, **kwargs):
        super().__init__(name, parent)
        # Additional initialization
```

### Loading Components from YAML

Define your system's components in a YAML file for easy configuration and modification.

**components.yaml**

```yaml
components:
  - name: component_a
    class: MyMicroComponent
    parameters:
      param1: value1

  - name: component_b
    class: MyMicroComponent
    parameters:
      param2: value2
    children:
      - name: component_c
        class: MyMicroComponent
        parameters:
          param3: value3
```

Load the components and start the system:

```python
from micro_registry.component_loader import load_components_and_start_system

load_components_and_start_system('components.yaml')
```

### Using the RegistryAPI and ComponentAPI

**micro-registry** includes built-in RESTful APIs for interacting with your components.

#### RegistryAPI

The `RegistryAPI` provides endpoints for:

- Listing registered classes.
- Listing instances.
- Loading instances from YAML.
- Filtering instances by base class.

#### ComponentAPI

The `ComponentAPI` allows you to:

- Retrieve component hierarchies.
- Get and update component attributes.
- Invoke component methods.

**Example:**

```python
from micro_registry.registry_rest_api import RegistryRestApi
from micro_registry.component_rest_api import ComponentRestApi

# Initialize the Registry API
registry_api = RegistryRestApi(name='registry_api', host='0.0.0.0', port=8000)

# Add the Component API as a child
component_api = ComponentRestApi(name='component_api', parent=registry_api)

# Start the API server
registry_api.start()
```

### Full Example

**components.yaml**

```yaml
components:
  - name: registry_api
    class: RegistryRestApi
    parameters:
      host: "0.0.0.0"
      port: 8000
    children:
      - name: component_api
        class: ComponentRestApi

  - name: scheduler_main
    class: Scheduler
    children:
      - name: living_room_light
        class: Light
        parameters:
          location: "Living Room"
          brightness: 75

      - name: hallway_thermostat
        class: Thermostat
        parameters:
          location: "Hallway"
          temperature: 21.5

      - name: evening_lights_automation
        class: Automation
        parameters:
          action: "turn_on"
          target_devices:
            - "living_room_light"

      - name: morning_temperature_automation
        class: Automation
        parameters:
          action: "set_temperature"
          target_devices:
            - "hallway_thermostat"
          temperature: 23.0
```

**main.py**

```python
from micro_registry.component_loader import load_components_and_start_system

if __name__ == '__main__':
    load_components_and_start_system('components.yaml')
```

### Interacting with the API

Once your system is running, you can interact with it using the API.

- **List Instances**

  ```bash
  curl http://localhost:8000/api/v1/instances
  ```

- **Get Component Hierarchy**

  ```bash
  curl http://localhost:8000/api/v1/component/scheduler_main/hierarchy/
  ```

- **Update Component Property**

  ```bash
  curl -X POST http://localhost:8000/api/v1/component/living_room_light/update-property/ \
       -H 'Content-Type: application/json' \
       -d '{"property_name": "status", "value": "on"}'
  ```

## Advanced Usage

### Plugin Architecture

Load additional modules dynamically to extend the functionality of your system without modifying the core code.

```python
from micro_registry.registry import load_modules_from_directory

load_modules_from_directory('plugins')
```

### Custom Component Methods

Define custom methods in your components and expose them via the API.

```python
@register_class
class Device(MicroComponent):
    def __init__(self, name, device_type, location, **kwargs):
        super().__init__(name)
        self.device_type = device_type
        self.location = location

    def turn_on(self):
        print(f"{self.device_type.capitalize()} '{self.name}' at '{self.location}' is now ON.")

    def turn_off(self):
        print(f"{self.device_type.capitalize()} '{self.name}' at '{self.location}' is now OFF.")
```
## Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally.

   ```shell
   git clone https://github.com/yourusername/micro_registry.git
   ```

3. **Install development dependencies**.

   ```shell
   pip install -e .[dev]
   ```

4. **Create a new branch** for your feature or bugfix.

   ```shell
   git checkout -b feature/new-feature
   ```

5. **Make your changes**, write tests, and ensure all tests pass.

   ```shell
   flake8 .
   python -m unittest discover -s tests
   ```

6. **Commit your changes** with a descriptive commit message.

   ```shell
   git commit -am "Add new feature to improve X"
   ```

7. **Push to your fork** and **submit a pull request**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or contributions, reach out at aleksander.stanik@hammerheadsengineers.com.
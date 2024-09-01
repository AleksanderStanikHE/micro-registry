import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import argparse
from micro_registry.component_rest_api import ComponentRestApi
from micro_registry.registry_rest_api import RegistryRestApi
from micro_registry.component import MicroComponent, create_component
from micro_registry.registry import instance_registry, register_class, create_instance
from typing import List, Optional


class ComponentWithFloatList(MicroComponent):
    def __init__(self, name: str, parent, float_values: Optional[List[float]] = None):
        super().__init__(name, parent)
        self._float_values = float_values or []
        self._internal_value = 0

    @property
    def float_values(self) -> List[float]:
        return self._float_values

    @float_values.setter
    def float_values(self, values: List[float]):
        if not all(isinstance(v, float) for v in values):
            raise ValueError("All items in the list must be floats")
        self._float_values = values


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run MicroRegistry servers")
    parser.add_argument("--registry-host", type=str, default="127.0.0.1", help="Host for the Registry REST API")
    parser.add_argument("--registry-port", type=int, default=8001, help="Port for the Registry REST API")
    return parser.parse_args()


def main():
    args = parse_arguments()

    register_class(ComponentWithFloatList)
    register_class(ComponentRestApi)
    register_class(RegistryRestApi)
    register_class(MicroComponent)
    # Create the root component
    root_component = create_instance(class_name="MicroComponent", name="RootComponent")
    instance_registry['RootComponent'] = root_component

    # Initialize and start the Registry REST API
    registry_rest_api = create_component(
        class_name="RegistryRestApi",
        instance_name='RegistryRESTServer',
        parent_name="RootComponent",
        host=args.registry_host,
        port=args.registry_port
    )

    # Initialize and start the Component REST API
    create_component(
        class_name="ComponentRestApi",
        instance_name='ComponentRESTServer',
        parent_name="RegistryRESTServer",
    )

    create_component(
        class_name="ComponentWithFloatList",
        instance_name='PropertiesComponent',
        parent_name="RootComponent",
        float_values=[1.3, 23.7, 77.42, 1832.2]
    )

    # Start the servers in separate threads
    registry_rest_api.start()

    print(f"Registry REST API is running on http://{args.registry_host}:{args.registry_port}")


if __name__ == "__main__":
    main()

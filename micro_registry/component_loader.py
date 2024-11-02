#
# MIT License
#
# Copyright (c) 2024 Aleksander(Olek) Stanik
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction.
#
# See the LICENSE file for full license details.

import yaml
from micro_registry.registry import class_registry, instance_registry
from micro_registry.component import MicroComponent
from typing import Any, Dict, Optional


def load_components_and_start_system(yaml_file_path: str):
    with open(yaml_file_path, 'r') as file:
        data = yaml.safe_load(file)

    components_data = data.get('components', [])

    # Recursively create components and set up relationships
    for component_data in components_data:
        create_component_recursive(component_data)

    # Find root components (components without a parent)
    root_components = [instance for instance in instance_registry.values() if instance.parent is None]

    # Call 'prepare()' and 'start()' on roots
    for root in root_components:
        root.prepare()
        root.start()


def create_component_recursive(component_data: Dict[str, Any], parent: Optional[MicroComponent] = None):
    name = component_data['name']
    class_name = component_data['class']
    parameters = component_data.get('parameters', {})
    children_data = component_data.get('children', [])

    # Check if the class is registered
    if class_name not in class_registry:
        raise ValueError(f"Class '{class_name}' not found in the class registry.")

    cls = class_registry[class_name]['class']

    # Create an instance of the component
    instance = cls(name=name, parent=parent, **parameters)
    instance_registry[name] = instance

    # Recursively create children
    for child_data in children_data:
        create_component_recursive(child_data, parent=instance)

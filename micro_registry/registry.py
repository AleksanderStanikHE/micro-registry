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

import importlib
import importlib.util
import os
import sys

import yaml

class_registry = {}
instance_registry = {}


def register_class(cls=None, *, name=None):
    if cls is None:
        return lambda cls: register_class(cls, name=name)

    class_name = name if name else cls.__name__
    base_class = cls.__bases__[0].__name__
    class_registry[class_name] = {"class": cls, "base_class": base_class}
    return cls


def create_instance(class_name, **kwargs):
    if class_name in class_registry:
        cls = class_registry[class_name]["class"]
    else:
        # Attempt to dynamically import the class
        cls = dynamic_import(class_name)
        if cls is None:
            raise ValueError(f"Class {class_name} not found and could not be imported")
    return cls(**kwargs)


def dynamic_import(class_path):
    """Dynamically import a class from a module."""
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls
    except (ImportError, AttributeError, ValueError) as e:
        print(f"Error importing {class_path}: {e}")
        return None


def load_module_from_path(file_path: str, module_name: str = None):
    if not module_name:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_modules_from_directory(directory: str):
    directory_path = os.path.abspath(directory)
    if directory_path not in sys.path:
        sys.path.append(directory_path)

    for filename in os.listdir(directory_path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            load_module_from_path(os.path.join(directory_path, filename), module_name)


def get_classes_by_base(base_class_name: str):
    return {
        name: info["class"]
        for name, info in class_registry.items()
        if info["base_class"] == base_class_name
    }


def get_class_names_by_base(base_class_name: str):
    return [
        name
        for name, info in class_registry.items()
        if info["base_class"] == base_class_name
    ]


def load_instances_from_yaml(filename: str):
    with open(filename, "r") as file:
        load_instances_from_yaml_data(file)


def load_instances_from_yaml_data(yaml_data: str):
    data = yaml.safe_load(yaml_data)

    for instance_name, instance_info in data.items():
        class_name = instance_info["class"]
        parameters = instance_info.get("parameters", {})
        instance = create_instance(class_name, **parameters)
        instance_registry[instance_name] = instance


def filter_instances_by_base_class(base_class):
    filtered_instances = {}
    for instance_name, instance in instance_registry.items():
        if isinstance(instance, base_class):
            filtered_instances[instance_name] = instance
    return filtered_instances


def filter_instances_by_base_class_name(base_class_name):
    filtered_instances = {}
    for instance_name, instance in instance_registry.items():
        for instance_base_class in type(instance).__bases__:
            if instance_base_class.__name__ == base_class_name:
                filtered_instances[instance_name] = instance
    return filtered_instances

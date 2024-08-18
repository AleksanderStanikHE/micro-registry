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
    class_registry[class_name] = {'class': cls, 'base_class': base_class}
    return cls


def create_instance(class_name, **kwargs):
    if class_name in class_registry:
        cls = class_registry[class_name]['class']
        return cls(**kwargs)
    else:
        raise ValueError(f"Class {class_name} not found in registry")


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
    return {name: info['class'] for name, info in class_registry.items() if info['base_class'] == base_class_name}


def get_class_names_by_base(base_class_name: str):
    return [name for name, info in class_registry.items() if info['base_class'] == base_class_name]


def load_instances_from_yaml(filename: str):
    with open(filename, 'r') as file:
        data = yaml.safe_load(file)

        for instance_name, instance_info in data.items():
            class_name = instance_info['class']
            parameters = instance_info.get('parameters', {})
            instance = create_instance(class_name, **parameters)
            instance_registry[instance_name] = instance


def filter_instances_by_base_class(base_class):
    filtered_instances = {}
    for instance_name, instance in instance_registry.items():
        if isinstance(instance, base_class):
            filtered_instances[instance_name] = instance
    return filtered_instances

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

import logging
from typing import Optional

from micro_registry.registry import class_registry, instance_registry


class MicroComponent:
    def __init__(self, name: str, parent: Optional["MicroComponent"] = None):
        self.name = name
        self.parent = parent
        self.children = []
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}.{self.name}"
        )
        if parent:
            parent.add_child(self)

    def add_child(self, child: "MicroComponent"):
        # Prevent adding itself as a child
        if child is self:
            raise ValueError(f"Cannot add {self.name} as its own child.")
        if not isinstance(child, MicroComponent):
            raise ValueError("Only MicroComponent instances can be added as children.")
        if child not in self.children:
            self.children.append(child)
            child.parent = self

    def remove_child(self, child: "MicroComponent"):
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def get_children(self):
        return self.children

    def get_parent(self):
        return self.parent

    def get_hierarchy(self):
        return {
            "name": self.name,
            "children": [child.get_hierarchy() for child in self.children],
        }

    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()

    def prepare(self):
        """Prepare the component and propagate to children."""
        print(f"Preparing {self.name}")
        for child in self.children:
            child.prepare()

    def start(self):
        """Start the component and propagate to children."""
        print(f"Starting {self.name}")
        for child in self.children:
            child.start()

    def pause(self):
        """Pause the component and propagate to children."""
        print(f"Pausing {self.name}")
        for child in self.children:
            child.pause()

    def stop(self):
        """Stop the component and propagate to children."""
        print(f"Stopping {self.name}")
        for child in self.children:
            child.stop()

    def __repr__(self):
        return f"<MicroComponent(name={self.name})>"


def create_component(
    class_name: str, instance_name: str, parent_name: Optional[str] = None, **kwargs
) -> MicroComponent:
    """Create a component and optionally attach it to a parent."""
    if class_name not in class_registry:
        raise ValueError(f"Class {class_name} not found in registry")

    cls = class_registry[class_name]["class"]

    # Instantiate the component
    if "parent" in kwargs:
        kwargs.pop("parent")  # Remove 'parent' from kwargs if present

    # Instantiate the component
    if "name" in kwargs:
        kwargs.pop("name")  # Remove 'name' from kwargs if present

    parent_instance = instance_registry.get(parent_name) if parent_name else None
    instance = cls(name=instance_name, parent=parent_instance, **kwargs)
    instance_registry[instance_name] = instance

    return instance

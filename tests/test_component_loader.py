# tests/test_component_loader.py
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import sys
import unittest

from micro_registry.component import MicroComponent
from micro_registry.component_loader import create_component_recursive
from micro_registry.registry import instance_registry


# Mock classes
class MockParentComponent(MicroComponent):
    pass


class MockChildComponent(MicroComponent):
    pass


# Mock module setup
module_name = "mock_components"
sys.modules[module_name] = type(sys)(module_name)
setattr(sys.modules[module_name], "MockParentComponent", MockParentComponent)
setattr(sys.modules[module_name], "MockChildComponent", MockChildComponent)


class TestCreateComponentRecursive(unittest.TestCase):

    def setUp(self):
        # Clear the instance registry before each test
        instance_registry.clear()

    def test_create_registered_component(self):
        component_data = {
            "name": "parent_component",
            "class": "mock_components.MockParentComponent",
            "parameters": {},
            "children": [],
        }
        create_component_recursive(component_data)
        self.assertIn("parent_component", instance_registry)
        self.assertIsInstance(
            instance_registry["parent_component"], MockParentComponent
        )

    def test_create_unregistered_component(self):
        component_data = {
            "name": "parent_component",
            "class": "mock_components.MockParentComponent",
            "parameters": {},
            "children": [
                {
                    "name": "child_component",
                    "class": "mock_components.MockChildComponent",
                    "parameters": {},
                }
            ],
        }
        create_component_recursive(component_data)
        self.assertIn("child_component", instance_registry)
        self.assertIsInstance(instance_registry["child_component"], MockChildComponent)
        self.assertEqual(
            instance_registry["child_component"].parent,
            instance_registry["parent_component"],
        )

    def test_recursive_creation(self):
        component_data = {
            "name": "root_component",
            "class": "mock_components.MockParentComponent",
            "parameters": {},
            "children": [
                {
                    "name": "child_component",
                    "class": "mock_components.MockChildComponent",
                    "parameters": {},
                    "children": [
                        {
                            "name": "grandchild_component",
                            "class": "mock_components.MockChildComponent",
                            "parameters": {},
                        }
                    ],
                }
            ],
        }
        create_component_recursive(component_data)
        self.assertIn("grandchild_component", instance_registry)
        grandchild = instance_registry["grandchild_component"]
        child = instance_registry["child_component"]
        root = instance_registry["root_component"]
        self.assertIs(grandchild.parent, child)
        self.assertIs(child.parent, root)


if __name__ == "__main__":
    unittest.main()

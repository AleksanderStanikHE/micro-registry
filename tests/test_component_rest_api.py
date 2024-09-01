import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from micro_registry.component import MicroComponent  # Importing MicroComponent from component.py
from micro_registry.registry import instance_registry, class_registry, register_class


class TestComponentRestApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Cleanup the registry after tests
        instance_registry.clear()
        class_registry.clear()
        register_class(MicroComponent)
        from micro_registry.registry_rest_api import RegistryRestApi
        from micro_registry.component_rest_api import ComponentRestApi
        """Set up the ComponentRestApi and TestClient once for all tests."""
        # cls.api = ComponentRestApi()
        # cls.client = TestClient(cls.api.app)

        cls.registry_server = RegistryRestApi("Server", parent=None)
        cls.api = ComponentRestApi(name="ComponentRestApiExtension", parent=cls.registry_server)
        cls.client = TestClient(cls.api.app)
        cls.prefix = cls.api.prefix

    @classmethod
    def tearDownClass(cls):
        # Cleanup the registry after tests
        instance_registry.clear()
        class_registry.clear()

    def test_01_create_root_component(self):
        """Test creating the root component."""
        response = self.client.post(self.prefix + "/create-component/", json={
            "class_name": "MicroComponent",
            "instance_name": "RootComponent",
            "parameters": {"name": "RootComponent"}
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("RootComponent", instance_registry)
        self.assertIsNone(instance_registry["RootComponent"].parent)

    def test_02_create_child_component(self):
        """Test creating a child component."""
        response = self.client.post(self.prefix + "/create-component/", json={
            "class_name": "MicroComponent",
            "instance_name": "ChildComponent1",
            "parent_path": "RootComponent",
            "parameters": {"name": "ChildComponent1"}
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("ChildComponent1", instance_registry)
        self.assertEqual(instance_registry["ChildComponent1"].parent.name, "RootComponent")

    def test_03_create_grandchild_component(self):
        """Test creating a grandchild component."""
        response = self.client.post(self.prefix + "/create-component/", json={
            "class_name": "MicroComponent",
            "instance_name": "GrandChildComponent",
            "parent_path": "RootComponent/ChildComponent1",
            "parameters": {"name": "GrandChildComponent"}
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("GrandChildComponent", instance_registry)
        self.assertEqual(instance_registry["GrandChildComponent"].parent.name, "ChildComponent1")

    def test_04_get_component_hierarchy(self):
        """Test retrieving the hierarchy of the root component."""
        response = self.client.get(self.prefix + "/component/RootComponent/hierarchy/")
        self.assertEqual(response.status_code, 200)
        expected_hierarchy = {
            "name": "RootComponent",
            "children": [
                {
                    "name": "ChildComponent1",
                    "children": [
                        {
                            "name": "GrandChildComponent",
                            "children": []
                        }
                    ]
                }
            ]
        }
        self.assertEqual(response.json(), expected_hierarchy)

    def test_05_get_component_attributes(self):
        """Test retrieving the attributes of a child component."""
        response = self.client.get(self.prefix + "/component/RootComponent/ChildComponent1/attributes/")
        self.assertEqual(response.status_code, 200)

        # Expected structure based on the modified attributes retrieval
        expected_attributes = {
            "name": {
                "value": "ChildComponent1",
                "type": "str",
            },
            "parent": {
                "component_name": "RootComponent",
                "type": "MicroComponent",
            },
            "children": {
                "items": [{"type": "MicroComponent", "component_name": "GrandChildComponent"}],
                "type": "list",
            }
        }

        # Extract the actual attributes from the response
        actual_attributes = response.json().get("attributes", {})

        # Ensure that expected_attributes is a subset of actual_attributes
        for key, value in expected_attributes.items():
            self.assertIn(key, actual_attributes)
            self.assertEqual(actual_attributes[key], value)

    def test_06_get_all_component_information(self):
        """Test retrieving all information of a child component and its descendants."""
        response = self.client.get(self.prefix + "/component/RootComponent/ChildComponent1/all/")
        self.assertEqual(response.status_code, 200)

        expected_all_info = {
            "name": "ChildComponent1",
            "attributes": {
                "name": {
                    "value": "ChildComponent1",
                    "type": "str",
                },
                "parent": {
                    "component_name": "RootComponent",  # Parent should be the name of the parent component
                    "type": "MicroComponent",  # Assuming type here should be a string
                },
                "children": {
                    "items": [{"type": "MicroComponent", "component_name": "GrandChildComponent"}],
                    "type": "list",
                }
            },
            "children": [
                {
                    "name": "GrandChildComponent",
                    "attributes": {
                        "name": {
                            "value": "GrandChildComponent",
                            "type": "str",
                        },
                        "parent": {
                            "component_name": "ChildComponent1",  # Parent should be the name of the parent component
                            "type": "MicroComponent",  # Assuming type here should be a string
                        },
                        "children": {
                            "type": "list",
                            "items": []
                        },
                    },
                    "children": []
                }
            ]
        }

        # Extract the actual information from the response
        actual_info = response.json()

        # Function to recursively check if one dictionary is a subset of another
        def dict_contains_subset(subset, dictionary):
            for key, value in subset.items():
                self.assertIn(key, dictionary)
                if isinstance(value, dict):
                    self.assertIsInstance(dictionary[key], dict)
                    dict_contains_subset(value, dictionary[key])
                else:
                    self.assertEqual(dictionary[key], value)

        # Use the function to check the expected structure
        dict_contains_subset(expected_all_info['attributes'], actual_info['attributes'])

    def test_07_prepare_component(self):
        """Test preparing a child component and its children."""
        with patch('builtins.print') as mocked_print:
            response = self.client.post(self.prefix + "/component/RootComponent/ChildComponent1/prepare/")
            self.assertEqual(response.status_code, 200)
            mocked_print.assert_any_call("Preparing ChildComponent1")
            mocked_print.assert_any_call("Preparing GrandChildComponent")

    def test_08_start_component(self):
        """Test starting the root component and its children."""
        with patch('builtins.print') as mocked_print:
            response = self.client.post(self.prefix + "/component/RootComponent/start/")
            self.assertEqual(response.status_code, 200)
            mocked_print.assert_any_call("Starting RootComponent")
            mocked_print.assert_any_call("Starting ChildComponent1")
            mocked_print.assert_any_call("Starting GrandChildComponent")

    def test_09_pause_component(self):
        """Test pausing the root component and its children."""
        with patch('builtins.print') as mocked_print:
            response = self.client.post(self.prefix + "/component/RootComponent/pause/")
            self.assertEqual(response.status_code, 200)
            mocked_print.assert_any_call("Pausing RootComponent")
            mocked_print.assert_any_call("Pausing ChildComponent1")
            mocked_print.assert_any_call("Pausing GrandChildComponent")

    def test_10_stop_component(self):
        """Test stopping the root component and its children."""
        with patch('builtins.print') as mocked_print:
            response = self.client.post(self.prefix + "/component/RootComponent/stop/")
            self.assertEqual(response.status_code, 200)
            mocked_print.assert_any_call("Stopping RootComponent")
            mocked_print.assert_any_call("Stopping ChildComponent1")
            mocked_print.assert_any_call("Stopping GrandChildComponent")

    def test_11_create_component_non_existent_parent(self):
        """Test creating a component with a non-existent parent."""
        response = self.client.post(self.prefix + "/create-component/", json={
            "class_name": "MicroComponent",
            "instance_name": "OrphanComponent",
            "parent_path": "NonExistentComponent",
            "parameters": {"name": "OrphanComponent"}
        })
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("OrphanComponent", instance_registry)


def suite():
    """Define the test suite."""
    suite = unittest.TestSuite()
    suite.addTest(TestComponentRestApi("test_01_create_root_component"))
    suite.addTest(TestComponentRestApi("test_02_create_child_component"))
    suite.addTest(TestComponentRestApi("test_03_create_grandchild_component"))
    suite.addTest(TestComponentRestApi("test_04_get_component_hierarchy"))
    suite.addTest(TestComponentRestApi("test_05_get_component_attributes"))
    suite.addTest(TestComponentRestApi("test_06_get_all_component_information"))
    suite.addTest(TestComponentRestApi("test_07_prepare_component"))
    suite.addTest(TestComponentRestApi("test_08_start_component"))
    suite.addTest(TestComponentRestApi("test_09_pause_component"))
    suite.addTest(TestComponentRestApi("test_10_stop_component"))
    suite.addTest(TestComponentRestApi("test_11_create_component_non_existent_parent"))
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())

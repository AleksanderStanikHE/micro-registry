import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from micro_registry.component import MicroComponent
from micro_registry.registry_rest_api import RegistryRestApi
from micro_registry.registry import instance_registry


def is_subset(subset, superset):
    for key, value in subset.items():
        if key not in superset:
            return False
        if isinstance(value, dict) and isinstance(superset[key], dict):
            if not is_subset(value, superset[key]):
                return False
        elif value != superset[key]:
            return False
    return True


class TestRegistryRestApi(unittest.TestCase):
    def setUp(self):
        # Initialize the RegistryRestApi and TestClient
        self.registry_rest_api = RegistryRestApi(name="TestRegistry")
        self.client = TestClient(self.registry_rest_api.app)

        # Create a test component and add it to the instance registry
        self.test_component = MicroComponent(name="TestComponent")
        self.test_component.app = FastAPI()  # Non-serializable example
        self.test_component.host = "127.0.0.1"
        self.test_component.port = 8001
        self.test_component.children = [MicroComponent(name="ChildComponent")]
        self.test_component.parent = MicroComponent(name="ParentComponent")

        instance_registry["TestComponent"] = self.test_component

    def test_get_instance_attributes(self):
        # Test retrieving the attributes of the test component
        response = self.client.get("/api/v1/instance/TestComponent/attributes/")
        self.assertEqual(response.status_code, 200)

        expected_attributes = {
            "attributes": {
                "app": {
                    "type": "FastAPI",
                    "value": "<non-serializable: FastAPI>"
                },
                "host": {
                    "type": "str",
                    "value": "127.0.0.1"
                },
                "port": {
                    "type": "int",
                    "value": 8001
                },
                "children": {
                    "type": "list",
                    "items": [
                        {
                            "type": "MicroComponent",
                            "component_name": "ChildComponent"
                        }
                    ]
                },
                "parent": {
                    "type": "MicroComponent",
                    "component_name": "ParentComponent"
                },
                "name": {
                    "type": "str",
                    "value": "TestComponent"
                }
            }
        }

        self.assertTrue(is_subset(expected_attributes, response.json()), "expected is not contained within response")

    def test_update_instance_attributes(self):
        # Test updating attributes of the test component with the correct payload structure
        update_payload = {
            "attributes": {
                "host": {"value": "192.168.1.1"},  # Change the host
                "port": {"value": 9000},  # Change the port
                "name": {"value": "UpdatedComponent"}  # Change the name
            }
        }
        response = self.client.post("/api/v1/instance/TestComponent/attributes/update/", json=update_payload)
        self.assertEqual(response.status_code, 200)

        # Verify that attributes have been updated
        updated_attributes = self.client.get("/api/v1/instance/TestComponent/attributes/").json()["attributes"]
        self.assertEqual(updated_attributes["host"]["value"], "192.168.1.1")
        self.assertEqual(updated_attributes["port"]["value"], 9000)
        self.assertEqual(updated_attributes["name"]["value"], "UpdatedComponent")

    def test_update_invalid_attribute(self):
        # Test updating a non-existent attribute with the correct payload structure
        update_payload = {
            "attributes": {
                "non_existent_attr": {"value": "value"}
            }
        }
        response = self.client.post("/api/v1/instance/TestComponent/attributes/update/", json=update_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Attribute 'non_existent_attr' not found", response.json()["detail"][0])

    def test_partial_update_instance_attributes(self):
        # Test partially updating attributes (only update those that differ) with the correct payload structure
        update_payload = {
            "attributes": {
                "port": {"value": 8001},  # This should not cause an update since it's the same
                "name": {"value": "PartiallyUpdatedComponent"}  # This should cause an update
            }
        }
        response = self.client.post("/api/v1/instance/TestComponent/attributes/update/", json=update_payload)
        self.assertEqual(response.status_code, 200)

        # Verify that only the name attribute has been updated
        updated_attributes = self.client.get("/api/v1/instance/TestComponent/attributes/").json()["attributes"]
        self.assertEqual(updated_attributes["port"]["value"], 8001)  # unchanged
        self.assertEqual(updated_attributes["name"]["value"], "PartiallyUpdatedComponent")  # updated

    def tearDown(self):
        # Clean up after each test
        instance_registry.clear()


if __name__ == "__main__":
    unittest.main()

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from fastapi.testclient import TestClient
from micro_registry.component import MicroComponent
from micro_registry.registry_rest_api import RegistryRestApi
from micro_registry.registry import instance_registry
from typing import List, Optional


class ComponentWithFloatList(MicroComponent):
    def __init__(self, name: str, float_values: Optional[List[float]] = None):
        super().__init__(name)
        self._float_values = float_values or []

    @property
    def float_values(self) -> List[float]:
        return self._float_values

    @float_values.setter
    def float_values(self, values: List[float]):
        if not all(isinstance(v, float) for v in values):
            raise ValueError("All items in the list must be floats")
        self._float_values = values


class TestRegistryRestApi(unittest.TestCase):
    def setUp(self):
        # Initialize the RegistryRestApi and TestClient
        self.registry_rest_api = RegistryRestApi(name="TestRegistry")
        self.client = TestClient(self.registry_rest_api.app)

        # Create a test component with a list of floats and add it to the instance registry
        self.test_component = ComponentWithFloatList(name="TestComponentWithFloatList", float_values=[1.1, 2.2, 3.3])
        instance_registry["TestComponentWithFloatList"] = self.test_component

    def test_get_instance_attributes_with_float_list(self):
        # Test retrieving the attributes of the component with the float list property
        response = self.client.get("/api/v1/instance/TestComponentWithFloatList/attributes/")
        self.assertEqual(response.status_code, 200)

        expected_attributes = {
            "attributes": {
                "name": {
                    "type": "str",
                    "value": "TestComponentWithFloatList"
                },
                "float_values": {
                    "type": "list",
                    "value": [1.1, 2.2, 3.3],
                    "is_property": True,
                    "has_setter": True
                }
            }
        }
        self.assertDictEqual(response.json()["attributes"]["name"], expected_attributes["attributes"]["name"])
        self.assertDictEqual(response.json()["attributes"]["float_values"], expected_attributes["attributes"]["float_values"])

    def test_update_float_list_property(self):
        # Test updating the float list property of the component
        update_payload = {
            "attributes": {
                "float_values": {"value": [4.4, 5.5, 6.6]}  # Change the float list
            }
        }
        response = self.client.post("/api/v1/instance/TestComponentWithFloatList/attributes/update/", json=update_payload)
        self.assertEqual(response.status_code, 200)

        # Verify that the float list has been updated
        updated_attributes = self.client.get("/api/v1/instance/TestComponentWithFloatList/attributes/").json()["attributes"]
        self.assertEqual(updated_attributes["float_values"]["value"], [4.4, 5.5, 6.6])

    def test_invalid_float_list_update(self):
        # Test attempting to update the float list property with invalid data
        update_payload = {
            "attributes": {
                "float_values": {"value": [4.4, "not_a_float", 6.6]}  # Invalid update
            }
        }
        response = self.client.post("/api/v1/instance/TestComponentWithFloatList/attributes/update/", json=update_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to update", response.json()["detail"][0])

    def tearDown(self):
        # Clean up after each test
        instance_registry.clear()


if __name__ == "__main__":
    unittest.main()

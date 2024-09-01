import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from fastapi.testclient import TestClient
from micro_registry.registry import instance_registry, register_class, class_registry


class TestComponentTree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Cleanup the registry after tests
        instance_registry.clear()
        class_registry.clear()
        from micro_registry.registry_rest_api import RegistryRestApi
        from micro_registry.component_rest_api import ComponentRestApi
        from custom_components import SensorComponent, ActuatorComponent, ControllerComponent

        register_class(SensorComponent)
        register_class(ActuatorComponent)
        register_class(ControllerComponent)
        cls.registry_server = RegistryRestApi("Server", parent=None)
        cls.api = ComponentRestApi(name="ComponentRestApiExtension", parent=cls.registry_server)
        cls.client = TestClient(cls.api.app)
        cls.prefix = cls.api.prefix

    @classmethod
    def tearDownClass(cls):
        # Cleanup the registry after tests
        instance_registry.clear()
        class_registry.clear()

    def test_01_create_controller_component(self):
        """Test creating the controller component."""
        response = self.client.post(self.prefix + "/create-component/", json={
            "class_name": "ControllerComponent",
            "instance_name": "MainController",
            "parameters": {"name": "MainController", "setpoint": 100.0}
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("MainController", instance_registry)

    def test_02_create_sensor_component(self):
        """Test creating the sensor component as a child of the controller."""
        response = self.client.post(self.prefix + "/create-component/", json={
            "class_name": "SensorComponent",
            "instance_name": "TemperatureSensor",
            "parent_path": "MainController",
            "parameters": {"name": "TemperatureSensor", "reading": 25.5}
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("TemperatureSensor", instance_registry)

    def test_03_create_actuator_component(self):
        """Test creating the actuator component as a child of the controller."""
        response = self.client.post(self.prefix + "/create-component/", json={
            "class_name": "ActuatorComponent",
            "instance_name": "CoolingFan",
            "parent_path": "MainController",
            "parameters": {"name": "CoolingFan", "state": False}
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("CoolingFan", instance_registry)

    def test_04_get_controller_hierarchy(self):
        """Test retrieving the hierarchy of the controller component."""
        response = self.client.get(self.prefix + "/component/MainController/hierarchy/")
        self.assertEqual(response.status_code, 200)
        expected_hierarchy = {
            "name": "MainController",
            "children": [
                {
                    "name": "TemperatureSensor",
                    "children": []
                },
                {
                    "name": "CoolingFan",
                    "children": []
                }
            ]
        }
        self.assertEqual(response.json(), expected_hierarchy)

    def test_05_read_sensor_property(self):
        """Test reading the 'reading' property of the sensor component."""
        response = self.client.get(self.prefix + "/component/MainController/TemperatureSensor/attributes/")
        self.assertEqual(response.status_code, 200)
        attributes = response.json()["attributes"]
        self.assertIn("reading", attributes)
        self.assertEqual(attributes["reading"]["value"], 25.5)
        self.assertEqual(attributes["reading"]["type"], "float")
        self.assertTrue(attributes["reading"]["is_property"])
        self.assertTrue(attributes["reading"]["has_setter"])

    def test_06_read_actuator_property(self):
        """Test reading the 'state' property of the actuator component."""
        response = self.client.get(self.prefix + "/component/MainController/CoolingFan/attributes/")
        self.assertEqual(response.status_code, 200)
        attributes = response.json()["attributes"]
        self.assertIn("state", attributes)
        self.assertFalse(attributes["state"]["value"])
        self.assertEqual(attributes["state"]["type"], "bool")
        self.assertTrue(attributes["state"]["is_property"])
        self.assertTrue(attributes["state"]["has_setter"])

    def test_07_update_sensor_property(self):
        """Test updating the 'reading' property of the sensor component."""
        response = self.client.post(self.prefix + "/component/MainController/TemperatureSensor/update-property/", json={
            "property_name": "reading",
            "value": 30.0
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(instance_registry["TemperatureSensor"].reading, 30.0)

    def test_08_update_actuator_property(self):
        """Test updating the 'state' property of the actuator component."""
        response = self.client.post(self.prefix + "/component/MainController/CoolingFan/update-property/", json={
            "property_name": "state",
            "value": True
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(instance_registry["CoolingFan"].state)

    def test_09_update_controller_property(self):
        """Test updating the 'setpoint' property of the controller component."""
        response = self.client.post(self.prefix + "/component/MainController/update-property/", json={
            "property_name": "setpoint",
            "value": 80.0
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(instance_registry["MainController"].setpoint, 80.0)

    def test_10_invalid_sensor_reading(self):
        """Test that setting an invalid 'reading' value on the sensor raises an error."""
        response = self.client.post(self.prefix + "/component/MainController/TemperatureSensor/update-property/", json={
            "property_name": "reading",
            "value": -10.0
        })
        self.assertEqual(response.status_code, 400)

    def test_11_update_nonexistent_property(self):
        """Test trying to update a property that doesn't exist."""
        response = self.client.post(self.prefix + "/component/MainController/TemperatureSensor/update-property/", json={
            "property_name": "nonexistent_property",
            "value": 100
        })
        self.assertEqual(response.status_code, 404)

    def test_12_update_all_component_attributes(self):
        """Test updating multiple attributes of a component in one call."""
        response = self.client.post(self.prefix + "/component/MainController/TemperatureSensor/update-attributes/", json={
            "attributes": {
                "reading": 28.5,
                # "name": "NewTemperatureSensor"
            }
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(instance_registry["TemperatureSensor"].reading, 28.5)
        # self.assertEqual(instance_registry["TemperatureSensor"].name, "NewTemperatureSensor")

        # Ensure the instance is now accessible under the new name
        self.assertIn("TemperatureSensor", instance_registry)
        self.assertNotIn("NewTemperatureSensor", instance_registry)

    def test_13_update_all_component_attributes_with_errors(self):
        """Test updating multiple attributes with some errors."""
        response = self.client.post(self.prefix + "/component/MainController/TemperatureSensor/update-attributes/", json={
            "attributes": {
                "reading": -10.0,  # Invalid value, should raise an error
                # "name": "AnotherTemperatureSensor"
            }
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("reading", response.json()["detail"][0])
        self.assertIn("Value must be non-negative", response.json()["detail"][0]["reading"])

        # Ensure the name did not change due to the error
        # self.assertEqual(instance_registry["TemperatureSensor"].name, "AnotherTemperatureSensor")


def suite():
    """Define the test suite to order the tests."""
    suite = unittest.TestSuite()
    suite.addTest(TestComponentTree("test_01_create_controller_component"))
    suite.addTest(TestComponentTree("test_02_create_sensor_component"))
    suite.addTest(TestComponentTree("test_03_create_actuator_component"))
    suite.addTest(TestComponentTree("test_04_get_controller_hierarchy"))
    suite.addTest(TestComponentTree("test_05_read_sensor_property"))
    suite.addTest(TestComponentTree("test_06_read_actuator_property"))
    suite.addTest(TestComponentTree("test_07_update_sensor_property"))
    suite.addTest(TestComponentTree("test_08_update_actuator_property"))
    suite.addTest(TestComponentTree("test_09_update_controller_property"))
    suite.addTest(TestComponentTree("test_10_invalid_sensor_reading"))
    suite.addTest(TestComponentTree("test_11_update_nonexistent_property"))
    suite.addTest(TestComponentTree("test_12_update_all_component_attributes"))
    suite.addTest(TestComponentTree("test_13_update_all_component_attributes_with_errors"))
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())

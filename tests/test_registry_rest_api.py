import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from fastapi.testclient import TestClient
from micro_registry.registry_rest_api import RegistryRestApi  # Ensure this import matches the actual location of your RestApi class
from micro_registry.component import MicroComponent  # Importing MicroComponent from component.py
from micro_registry.registry import instance_registry, class_registry, register_class


class TestRestApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Cleanup the registry after tests
        instance_registry.clear()
        class_registry.clear()
        # Initialize the RestApi component and start the app
        cls.api_component = RegistryRestApi(name="TestAPI", host="127.0.0.1", port=8001)
        instance_registry["TestAPI"] = cls.api_component
        cls.client = TestClient(cls.api_component.app)
        cls.prefix = cls.api_component.prefix

        # Register some dummy classes for testing
        @register_class
        class TestComponent(MicroComponent):
            def __init__(self, name, value=0):
                super().__init__(name)
                self.value = value

        @register_class
        class AnotherComponent(MicroComponent):
            def __init__(self, name, data=""):
                super().__init__(name)
                self.data = data

    @classmethod
    def tearDownClass(cls):
        # Cleanup the registry after tests
        instance_registry.clear()
        class_registry.clear()

    def test_list_registered_classes(self):
        response = self.client.get(self.prefix + "/classes/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("TestComponent", response.json()["classes"])
        self.assertIn("AnotherComponent", response.json()["classes"])

    def test_list_registered_instances(self):
        # First, create an instance
        response = self.client.post(self.prefix + "/create-instance/", json={
            "class_name": "TestComponent",
            "instance_name": "test_instance",
            "parameters": {"name": "TestInstance", "value": 42}
        })

        # Print response for debugging
        print("POST response:", response.status_code, response.json())

        # Check that the POST request was successful
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.prefix + "/instances/")

        # Print response for debugging
        print("GET response:", response.status_code, response.json())

        self.assertEqual(response.status_code, 200)
        self.assertIn("test_instance", response.json()["instances"])

    def test_create_instance(self):
        response = self.client.post(self.prefix + "/create-instance/", json={
            "class_name": "AnotherComponent",
            "instance_name": "another_instance",
            "parameters": {"name": "AnotherInstance", "data": "sample data"}
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("another_instance", instance_registry)
        self.assertEqual(instance_registry["another_instance"].data, "sample data")

    def test_load_instances_from_yaml_string(self):
        yaml_content = """
        test_instance_1:
          class: TestComponent
          parameters:
            name: TestInstance1
            value: 10
        test_instance_2:
          class: AnotherComponent
          parameters:
            name: TestInstance2
            data: "Some data"
        """
        response = self.client.post(self.prefix + "/load-instances-from-yaml/", json={"yaml_content": yaml_content})
        self.assertEqual(response.status_code, 200)
        self.assertIn("test_instance_1", instance_registry)
        self.assertIn("test_instance_2", instance_registry)
        self.assertEqual(instance_registry["test_instance_1"].value, 10)
        self.assertEqual(instance_registry["test_instance_2"].data, "Some data")

    def test_load_module(self):
        # Define the path to the test module relative to the current directory
        file_path = os.path.join(os.path.dirname(__file__), "temp_module.py")

        # Test loading the module
        response = self.client.post(self.prefix + "/load-module/", json={"file_path": file_path})
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_load_modules_from_directory(self):
        # Assume test_directory exists and contains valid Python modules
        test_path = os.path.dirname(__file__)
        response = self.client.post(self.prefix + "/load-modules-from-directory/", json={"directory": test_path})
        self.assertEqual(response.status_code, 200)

    def test_get_classes_by_base_class(self):
        response = self.client.get(self.prefix + "/classes-by-base/", params={"base_class_name": "MicroComponent"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("TestComponent", response.json()["classes"])

    def test_get_class_names_by_base_class(self):
        response = self.client.get(self.prefix + "/class-names-by-base/", params={"base_class_name": "MicroComponent"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("TestComponent", response.json()["class_names"])

    def test_filter_instances_by_base_class(self):

        self.client.post(self.prefix + "/create-instance/", json={
            "class_name": "TestComponent",
            "instance_name": "attribute_instance_new",
            "parameters": {"name": "AttributeInstance", "value": 99}
        })

        response = self.client.get(self.prefix + "/instance/attribute_instance_new/attributes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attributes"]["value"]["value"], 99)

        response = self.client.get(self.prefix + "/filter-instances-by-base-class/", params={"base_class_name": "MicroComponent"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("attribute_instance_new", response.json()["instances"])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestRestApi('test_list_registered_classes'))
    suite.addTest(TestRestApi('test_create_instance'))
    suite.addTest(TestRestApi('test_list_registered_instances'))
    suite.addTest(TestRestApi('test_load_instances_from_yaml_string'))
    suite.addTest(TestRestApi('test_load_module'))
    suite.addTest(TestRestApi('test_load_modules_from_directory'))
    suite.addTest(TestRestApi('test_get_classes_by_base_class'))
    suite.addTest(TestRestApi('test_get_class_names_by_base_class'))
    suite.addTest(TestRestApi('test_filter_instances_by_base_class'))

    runner = unittest.TextTestRunner()
    runner.run(suite)

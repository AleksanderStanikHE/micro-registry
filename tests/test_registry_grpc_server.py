import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
import grpc
import micro_registry.registry_pb2 as registry_pb2
import micro_registry.registry_pb2_grpc as registry_pb2_grpc


class TestRegistryService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.channel = grpc.insecure_channel('localhost:50051')
        cls.stub = registry_pb2_grpc.RegistryServiceStub(cls.channel)

    def test_01_register_class(self):
        response = self.stub.RegisterClass(registry_pb2.RegisterClassRequest(class_name="TestComponent", base_class_name="MicroComponent"))
        self.assertEqual(response.message, "Class TestComponent registered successfully.")

    def test_02_create_instance(self):
        response = self.stub.CreateInstance(registry_pb2.CreateInstanceRequest(
            class_name="TestComponent",
            instance_name="test_instance",
            parameters={}
        ))
        self.assertEqual(response.message, "Instance test_instance created successfully.")

    def test_03_get_instance_attributes(self):
        response = self.stub.GetInstanceAttributes(registry_pb2.GetInstanceAttributesRequest(instance_name="test_instance"))
        self.assertIn("name", response.attributes)
        self.assertEqual(response.attributes["name"], "test_instance")

    # def test_list_registered_classes(self):
    #     response = self.stub.ListRegisteredClasses(registry_pb2.Empty())
    #     self.assertIn("TestComponent", response.class_names)

    # def test_list_registered_instances(self):
    #     response = self.stub.ListRegisteredInstances(registry_pb2.Empty())
    #     self.assertIn("test_instance", response.instance_names)


if __name__ == '__main__':
    unittest.main()

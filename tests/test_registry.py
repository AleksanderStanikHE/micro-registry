import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from micro_registry.registry import register_class, create_instance, class_registry, instance_registry, load_instances_from_yaml


class TestMicroRegistry(unittest.TestCase):
    def setUp(self):
        # Reset the registries before each test
        class_registry.clear()
        instance_registry.clear()

    def test_register_class(self):
        @register_class
        class MyClass:
            pass

        self.assertIn('MyClass', class_registry)
        self.assertEqual(class_registry['MyClass']['class'], MyClass)

    def test_create_instance(self):
        @register_class
        class MyClass:
            def __init__(self, param1=None):
                self.param1 = param1

        instance = create_instance('MyClass', param1='value1')
        self.assertEqual(instance.param1, 'value1')

    def test_load_instances_from_yaml(self):
        @register_class
        class MyClass:
            def __init__(self, param1=None):
                self.param1 = param1

        config_file_path = os.path.join(os.path.dirname(__file__), 'temp.yaml')
        load_instances_from_yaml(config_file_path)
        instance = instance_registry['MyInstance']
        self.assertEqual(instance.param1, 'value1')


if __name__ == '__main__':
    unittest.main()

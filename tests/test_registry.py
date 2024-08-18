import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from micro_registry.registry import (
    register_class,
    create_instance,
    class_registry,
    instance_registry,
    load_instances_from_yaml,
    filter_instances_by_base_class,
)


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

    def test_filter_instances_by_base_class(self):
        # Define a base class and a derived class
        @register_class
        class BaseClass:
            def __init__(self, base_param=None):
                self.base_param = base_param

        @register_class
        class DerivedClass(BaseClass):
            def __init__(self, base_param=None, derived_param=None):
                super().__init__(base_param)
                self.derived_param = derived_param

        # Create instances
        base_instance = create_instance('BaseClass', base_param='base_value')
        derived_instance = create_instance('DerivedClass', base_param='base_value', derived_param='derived_value')

        # Register instances manually to simulate loaded instances
        instance_registry['BaseInstance'] = base_instance
        instance_registry['DerivedInstance'] = derived_instance

        # Filter instances by BaseClass
        filtered_instances = filter_instances_by_base_class(BaseClass)

        # Assert that both the base class and derived class instances are returned
        self.assertIn('BaseInstance', filtered_instances)
        self.assertIn('DerivedInstance', filtered_instances)

        # Assert that the filtered instances are of the correct types
        self.assertIsInstance(filtered_instances['BaseInstance'], BaseClass)
        self.assertIsInstance(filtered_instances['DerivedInstance'], DerivedClass)


if __name__ == '__main__':
    unittest.main()

# tests/test_dynamic_import.py
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import sys
import unittest

from micro_registry.registry import dynamic_import


# Mock module and class for testing
class MockClass:
    pass


module_name = "test_module"
sys.modules[module_name] = type(sys)(module_name)
setattr(sys.modules[module_name], "MockClass", MockClass)


class TestDynamicImport(unittest.TestCase):

    def test_dynamic_import_success(self):
        cls = dynamic_import(f"{module_name}.MockClass")
        self.assertEqual(cls, MockClass)

    def test_dynamic_import_module_not_found(self):
        cls = dynamic_import("nonexistent_module.MockClass")
        self.assertIsNone(cls)

    def test_dynamic_import_class_not_found(self):
        cls = dynamic_import(f"{module_name}.NonExistentClass")
        self.assertIsNone(cls)


if __name__ == "__main__":
    unittest.main()

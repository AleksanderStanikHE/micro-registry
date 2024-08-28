import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from unittest.mock import patch
from micro_registry.component import MicroComponent  # Importing MicroComponent from component.py
from micro_registry.registry import class_registry, instance_registry


class TestMicroComponent(unittest.TestCase):
    @classmethod
    def setUp(self):
        # Reset the registries before each test
        class_registry.clear()
        instance_registry.clear()

    @classmethod
    def tearDownClass(cls):
        # Cleanup the registry after tests
        instance_registry.clear()
        class_registry.clear()

    def test_initialization(self):
        """Test that a MicroComponent is initialized correctly."""
        component = MicroComponent(name="Component1")
        self.assertEqual(component.name, "Component1")
        self.assertIsNone(component.parent)
        self.assertEqual(component.get_children(), [])

    def test_add_child(self):
        """Test adding a child to a MicroComponent."""
        parent = MicroComponent(name="ParentComponent")
        child = MicroComponent(name="ChildComponent", parent=parent)

        self.assertEqual(len(parent.get_children()), 1)
        self.assertIn(child, parent.get_children())
        self.assertEqual(child.parent, parent)

    def test_remove_child(self):
        """Test removing a child from a MicroComponent."""
        parent = MicroComponent(name="ParentComponent")
        child = MicroComponent(name="ChildComponent", parent=parent)

        # Remove the child
        parent.remove_child(child)
        self.assertEqual(parent.get_children(), [])
        self.assertIsNone(child.parent)  # The child's parent should now be None

    def test_get_hierarchy(self):
        """Test the hierarchy method of a MicroComponent."""
        root = MicroComponent(name="RootComponent")
        child1 = MicroComponent(name="ChildComponent1", parent=root)
        MicroComponent(name="ChildComponent2", parent=root)
        MicroComponent(name="GrandChildComponent", parent=child1)

        hierarchy = root.get_hierarchy()
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
                },
                {
                    "name": "ChildComponent2",
                    "children": []
                }
            ]
        }
        self.assertEqual(hierarchy, expected_hierarchy)

    def test_get_parent(self):
        """Test retrieving the parent of a MicroComponent."""
        parent = MicroComponent(name="ParentComponent")
        child = MicroComponent(name="ChildComponent", parent=parent)

        self.assertEqual(child.get_parent(), parent)

    def test_get_root(self):
        """Test retrieving the root component of a hierarchy."""
        root = MicroComponent(name="RootComponent")
        child = MicroComponent(name="ChildComponent", parent=root)
        grandchild = MicroComponent(name="GrandChildComponent", parent=child)

        self.assertEqual(grandchild.get_root(), root)
        self.assertEqual(child.get_root(), root)
        self.assertEqual(root.get_root(), root)

    def test_prepare_propagation(self):
        """Test the prepare method and its propagation to children."""
        root = MicroComponent(name="RootComponent")
        child1 = MicroComponent(name="ChildComponent1", parent=root)
        MicroComponent(name="ChildComponent2", parent=root)
        MicroComponent(name="GrandChildComponent", parent=child1)

        with patch('builtins.print') as mocked_print:
            root.prepare()
            mocked_print.assert_any_call("Preparing RootComponent")
            mocked_print.assert_any_call("Preparing ChildComponent1")
            mocked_print.assert_any_call("Preparing GrandChildComponent")
            mocked_print.assert_any_call("Preparing ChildComponent2")

    def test_start_propagation(self):
        """Test the start method and its propagation to children."""
        root = MicroComponent(name="RootComponent")
        child1 = MicroComponent(name="ChildComponent1", parent=root)
        MicroComponent(name="ChildComponent2", parent=root)
        MicroComponent(name="GrandChildComponent", parent=child1)

        with patch('builtins.print') as mocked_print:
            root.start()
            mocked_print.assert_any_call("Starting RootComponent")
            mocked_print.assert_any_call("Starting ChildComponent1")
            mocked_print.assert_any_call("Starting GrandChildComponent")
            mocked_print.assert_any_call("Starting ChildComponent2")

    def test_pause_propagation(self):
        """Test the pause method and its propagation to children."""
        root = MicroComponent(name="RootComponent")
        child1 = MicroComponent(name="ChildComponent1", parent=root)
        MicroComponent(name="ChildComponent2", parent=root)
        MicroComponent(name="GrandChildComponent", parent=child1)

        with patch('builtins.print') as mocked_print:
            root.pause()
            mocked_print.assert_any_call("Pausing RootComponent")
            mocked_print.assert_any_call("Pausing ChildComponent1")
            mocked_print.assert_any_call("Pausing GrandChildComponent")
            mocked_print.assert_any_call("Pausing ChildComponent2")

    def test_stop_propagation(self):
        """Test the stop method and its propagation to children."""
        root = MicroComponent(name="RootComponent")
        child1 = MicroComponent(name="ChildComponent1", parent=root)
        MicroComponent(name="ChildComponent2", parent=root)
        MicroComponent(name="GrandChildComponent", parent=child1)

        with patch('builtins.print') as mocked_print:
            root.stop()
            mocked_print.assert_any_call("Stopping RootComponent")
            mocked_print.assert_any_call("Stopping ChildComponent1")
            mocked_print.assert_any_call("Stopping GrandChildComponent")
            mocked_print.assert_any_call("Stopping ChildComponent2")

    def test_circular_reference_protection(self):
        """Test that adding a component as its own parent does not create a circular reference."""
        component = MicroComponent(name="Component")
        with self.assertRaises(ValueError):
            component.add_child(component)  # Should raise an error

    def test_remove_nonexistent_child(self):
        """Test that removing a child that isn't present doesn't cause issues."""
        parent = MicroComponent(name="ParentComponent")
        child = MicroComponent(name="ChildComponent")

        # Attempt to remove a child that was never added
        parent.remove_child(child)
        self.assertEqual(parent.get_children(), [])  # No children should be present


if __name__ == "__main__":
    unittest.main()

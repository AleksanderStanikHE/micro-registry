# test_smart_hub.py

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import unittest
import time
from micro_registry.component_loader import load_components_and_start_system
from micro_registry.registry import instance_registry, load_modules_from_directory
from fastapi.testclient import TestClient
import threading


class TestSmartHubApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry_directory = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'micro_registry')
        load_modules_from_directory(registry_directory)
        load_modules_from_directory(os.path.dirname(__file__))
        # Load the components from the YAML file
        config_file_path = os.path.join(os.path.dirname(__file__), 'smart_hub.yaml')
        load_components_and_start_system(config_file_path)

        # Wait for the API server to start
        time.sleep(1)

        # Initialize the TestClient with the FastAPI app
        registry_api = instance_registry.get('registry_api')
        if registry_api and hasattr(registry_api, 'app'):
            cls.client = TestClient(registry_api.app)
        else:
            raise Exception("Registry API not initialized properly.")

    @classmethod
    def tearDownClass(cls):
        # Close the TestClient
        if hasattr(cls, 'client'):
            cls.client.close()

        # Stop the scheduler
        scheduler = instance_registry.get('scheduler_main')
        if scheduler:
            scheduler.stop()

        # Ensure all threads are terminated
        for thread in threading.enumerate():
            print(f"Thread {thread.name}: Daemon={thread.daemon}, Alive={thread.is_alive()}")

    def test_01_components_loaded(self):
        # Test that all components are loaded
        expected_components = [
            'registry_api',
            'component_api',
            'scheduler_main',
            'living_room_light',
            'hallway_thermostat',
            'evening_lights_automation',
            'morning_temperature_automation'
        ]
        for component_name in expected_components:
            with self.subTest(component=component_name):
                self.assertIn(component_name, instance_registry)
                component = instance_registry.get(component_name)
                self.assertIsNotNone(component)
                self.assertEqual(component.name, component_name)

    def test_02_device_attributes(self):
        # Test that devices have correct attributes
        light = instance_registry.get('living_room_light')
        thermostat = instance_registry.get('hallway_thermostat')

        self.assertEqual(light.device_type, 'light')
        self.assertEqual(light.location, 'Living Room')
        self.assertEqual(light.brightness, 75)

        self.assertEqual(thermostat.device_type, 'thermostat')
        self.assertEqual(thermostat.location, 'Hallway')
        self.assertEqual(thermostat.temperature, 21.5)

    def test_03_automation_targets(self):
        # Test that automations have correct target devices
        evening_automation = instance_registry.get('evening_lights_automation')
        morning_automation = instance_registry.get('morning_temperature_automation')

        # Prepare automations to resolve device references
        evening_automation.prepare()
        morning_automation.prepare()

        self.assertEqual(len(evening_automation.target_devices), 1)
        self.assertEqual(evening_automation.target_devices[0].name, 'living_room_light')

        self.assertEqual(len(morning_automation.target_devices), 1)
        self.assertEqual(morning_automation.target_devices[0].name, 'hallway_thermostat')

    def test_04_automation_execution(self):
        # Test execution of automations
        light = instance_registry.get('living_room_light')
        thermostat = instance_registry.get('hallway_thermostat')
        evening_automation = instance_registry.get('evening_lights_automation')
        morning_automation = instance_registry.get('morning_temperature_automation')

        # Ensure devices are in initial state
        light.status = 'off'
        thermostat.temperature = 21.5

        # Execute automations
        evening_automation.execute()
        morning_automation.execute()

        # Check if the automations performed the actions
        self.assertEqual(light.status, 'on')
        self.assertEqual(thermostat.temperature, 23.0)

    def test_05_api_root(self):
        # Test the API root endpoint
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to Registry API version v1"})

    def test_06_list_components_api(self):
        # Test listing components via API
        response = self.client.get('/api/v1/components')
        self.assertEqual(response.status_code, 200)
        components = response.json().get('components', [])
        expected_components = [
            'registry_api',
            'component_api',
            'scheduler_main',
            'living_room_light',
            'hallway_thermostat',
            'evening_lights_automation',
            'morning_temperature_automation'
        ]
        for component_name in expected_components:
            with self.subTest(component=component_name):
                self.assertIn(component_name, components)

    def test_07_get_component_attributes_api(self):
        # Test getting component attributes via API
        response = self.client.get('/api/v1/component/scheduler_main/living_room_light/attributes/')
        self.assertEqual(response.status_code, 200)
        attributes = response.json().get('attributes', {})

        self.assertEqual(attributes.get('name', {}).get('value'), 'living_room_light')
        self.assertEqual(attributes.get('device_type', {}).get('value'), 'light')
        self.assertEqual(attributes.get('location', {}).get('value'), 'Living Room')

    def test_08_update_device_status_api(self):
        # Test updating device status via API
        data = {
            "property_name": "status",
            "value": "off"
        }
        response = self.client.post('/api/v1/component/living_room_light/update-property/', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('message'), "Property 'status' updated successfully")

        # Verify the status is updated
        light = instance_registry.get('living_room_light')
        self.assertEqual(light.status, 'off')

    def test_10_component_not_found_api(self):
        # Test API response for a non-existent component
        response = self.client.get('/api/v1/component/non_existent_component/attributes')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get('detail'), "Component not found")

    def test_11_scheduler_start(self):
        # Test that the scheduler is running
        scheduler = instance_registry.get('scheduler_main')
        print("Thread is alive:", scheduler.thread.is_alive())
        self.assertTrue(scheduler.thread.is_alive())

    def test_12_schedule_automation(self):
        # Test scheduling an automation
        scheduler = instance_registry.get('scheduler_main')
        test_automation = instance_registry.get('evening_lights_automation')

        # Schedule the automation to run after 1 second
        scheduler.schedule_automation(test_automation, delay_seconds=1)

        # Wait for 2 seconds to ensure automation executes
        time.sleep(2)

        # Check if the automation was executed
        light = instance_registry.get('living_room_light')
        self.assertEqual(light.status, 'on')


if __name__ == '__main__':
    unittest.main()

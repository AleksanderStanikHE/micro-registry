# automations.py
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from micro_registry.registry import register_class, instance_registry
from micro_registry.component import MicroComponent
from typing import List


@register_class
class Automation(MicroComponent):
    def __init__(
        self,
        name: str,
        parent=None,
        action: str = '',
        target_devices: List[str] = None,
        temperature: float = None,
        **kwargs
    ):
        super().__init__(name, parent)
        self.action = action
        self.target_device_names = target_devices or []
        self.target_devices = []
        self.temperature = temperature  # Now correctly assigning temperature
        # You can assign other specific parameters here as needed

    def prepare(self):
        super().prepare()
        # Resolve device references
        self.target_devices = []
        for device_name in self.target_device_names:
            device = instance_registry.get(device_name)
            if device:
                self.target_devices.append(device)
            else:
                print(f"Device '{device_name}' not found for automation '{self.name}'.")

    def start(self):
        super().start()
        print(f"Automation '{self.name}' is starting.")
        self.execute()

    def execute(self):
        print(f"Executing automation '{self.name}' with action '{self.action}'.")
        for device in self.target_devices:
            if self.action == 'turn_on':
                device.turn_on()
            elif self.action == 'turn_off':
                device.turn_off()
            elif self.action == 'set_temperature':
                if self.temperature is not None and hasattr(device, 'set_temperature'):
                    device.set_temperature(self.temperature)
                else:
                    print(f"Temperature not specified or device '{device.name}' cannot set temperature.")
            else:
                print(f"Unknown action '{self.action}' for automation '{self.name}'.")

# devices.py

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from micro_registry.registry import register_class
from micro_registry.component import MicroComponent


@register_class
class Device(MicroComponent):
    def __init__(self, name: str, parent=None, device_type: str = '', location: str = '', **kwargs):
        super().__init__(name, parent)
        self.device_type = device_type
        self.location = location
        self.status = 'off'

    def turn_on(self):
        self.status = 'on'
        print(f"{self.device_type.capitalize()} '{self.name}' at '{self.location}' is turned on.")

    def turn_off(self):
        self.status = 'off'
        print(f"{self.device_type.capitalize()} '{self.name}' at '{self.location}' is turned off.")


@register_class
class Light(Device):
    def __init__(self, name: str, parent=None, brightness: int = 100, **kwargs):
        super().__init__(name, parent, device_type='light', **kwargs)
        self.brightness = brightness


@register_class
class Thermostat(Device):
    def __init__(self, name: str, parent=None, temperature: float = 20.0, **kwargs):
        super().__init__(name, parent, device_type='thermostat', **kwargs)
        self.temperature = temperature

    def set_temperature(self, temperature: float):
        self.temperature = temperature
        print(f"Thermostat '{self.name}' set to {self.temperature}°C.")

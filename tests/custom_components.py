# custom_components.py
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from micro_registry.component import MicroComponent
from typing import Optional


class SensorComponent(MicroComponent):
    def __init__(self, name: str, parent: Optional[MicroComponent] = None, reading: float = 0.0):
        super().__init__(name, parent)
        self._reading = reading

    @property
    def reading(self):
        return self._reading

    @reading.setter
    def reading(self, value: float):
        if value < 0.0:
            raise ValueError("Reading must be non-negative")
        self._reading = value


class ActuatorComponent(MicroComponent):
    def __init__(self, name: str, parent: Optional[MicroComponent] = None, state: bool = False):
        super().__init__(name, parent)
        self._state = state

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: bool):
        self._state = value


class ControllerComponent(MicroComponent):
    def __init__(self, name: str, parent: Optional[MicroComponent] = None, setpoint: float = 0.0):
        super().__init__(name, parent)
        self._setpoint = setpoint

    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value: float):
        self._setpoint = value

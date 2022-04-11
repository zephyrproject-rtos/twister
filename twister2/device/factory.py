from __future__ import annotations

import logging
from typing import Type

from twister2.device.device_abstract import DeviceAbstract
from twister2.device.hardware_adapter import HardwareAdapter
from twister2.device.simulator_adapter import SimulatorAdapter

logger = logging.getLogger(__name__)


class DeviceFactory:
    _devices: dict[str, Type[DeviceAbstract]] = {}

    @classmethod
    def discover(cls):
        """Return available devices."""

    @classmethod
    def register_device_class(cls, name: str, klass: Type[DeviceAbstract]):
        if name not in cls._devices:
            cls._devices[name] = klass

    @classmethod
    def get_device(cls, name: str) -> Type[DeviceAbstract]:
        logger.debug('Get device type "%s"', name)
        return cls._devices[name]


DeviceFactory.register_device_class('simulator', SimulatorAdapter)
DeviceFactory.register_device_class('hardware', HardwareAdapter)

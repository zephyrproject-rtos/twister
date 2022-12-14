import logging
from typing import Generator, Type

import pytest

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.device.device_abstract import DeviceAbstract
from twister2.device.factory import DeviceFactory
from twister2.fixtures.common import TestSetupManager

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def dut(
        builder: BuilderAbstract, setup_manager: TestSetupManager
) -> Generator[DeviceAbstract, None, None]:
    """Return device instance."""
    spec = setup_manager.specification
    twister_config = setup_manager.twister_config
    build_dir = setup_manager.specification.build_dir
    platform = setup_manager.platform

    if not (device_type := setup_manager.get_device_type()):
        msg = f'Handling of device type {platform.type} not implemented yet.'
        logger.error(msg)
        pytest.fail(msg)

    device_class: Type[DeviceAbstract] = DeviceFactory.get_device(device_type)
    hardware_map = twister_config.get_hardware_map(platform=spec.platform)

    device = device_class(
        twister_config=twister_config,
        hardware_map=hardware_map
    )

    # check if test should be executed, if not than do not flash/run code on device
    if setup_manager.is_executable:
        device.connect()
        device.generate_command(build_dir)
        device.flash_and_run(timeout=spec.timeout)
    yield device
    if setup_manager.is_executable:
        device.disconnect()
        device.stop()

import logging
from typing import Type

import pytest

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.device.device_abstract import DeviceAbstract
from twister2.device.factory import DeviceFactory
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def dut(request: pytest.FixtureRequest, builder: BuilderAbstract) -> DeviceAbstract:
    """Return device instance."""
    twister_config: TwisterConfig = request.config.twister_config
    function = request.function
    build_dir = function.spec.build_dir

    platform = twister_config.get_platform(request.function.spec.platform)

    # TODO: implement
    if twister_config.device_testing:
        device_type = 'hardware'
    elif platform.type == 'native':
        device_type = 'native'
    else:
        device_type = None

    device_class: Type[DeviceAbstract] = DeviceFactory.get_device(device_type)
    device = device_class(
        twister_config=twister_config,
        hardware_map=twister_config.get_hardware_map(platform=function.spec.platform)
    )

    if not twister_config.build_only:
        device.connect()
        device.flash(build_dir=build_dir, timeout=function.spec.timeout)
    yield device
    if not twister_config.build_only:
        device.disconnect()

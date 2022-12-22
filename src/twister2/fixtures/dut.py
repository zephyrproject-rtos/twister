import logging
from typing import Generator, Type

import pytest

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.device.device_abstract import DeviceAbstract
from twister2.device.factory import DeviceFactory
from twister2.exceptions import TwisterConfigurationException, TwisterRunException
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def dut(request: pytest.FixtureRequest, builder: BuilderAbstract) -> Generator[DeviceAbstract, None, None]:
    """Return device instance."""
    twister_config: TwisterConfig = request.config.twister_config  # type: ignore
    spec = request.session.specifications.get(request.node.nodeid)  # type: ignore
    if not spec:
        msg = f'Could not find test specification for test {request.node.nodeid}'
        logger.error(msg)
        raise TwisterConfigurationException(msg)

    build_dir = spec.build_dir

    platform = twister_config.get_platform(spec.platform)

    # TODO: implement
    if twister_config.device_testing:
        device_type = 'hardware'
    elif platform.type == 'native':
        device_type = 'native'
    else:
        msg = f'Handling of device type {platform.type} not implemented yet.'
        logger.error(msg)
        pytest.fail(msg)

    device_class: Type[DeviceAbstract] = DeviceFactory.get_device(device_type)
    hardware_map = twister_config.get_hardware_map(platform=spec.platform)

    if device_type == 'hardware' and hardware_map is None:
        msg = f'There is no available or connected device for the platform {spec.platform} in hardware map'
        logger.error(msg)
        raise TwisterRunException(msg)

    device = device_class(
        twister_config=twister_config,
        hardware_map=hardware_map
    )

    if not twister_config.build_only:
        device.connect()
        device.generate_command(build_dir)
        device.flash_and_run(timeout=spec.timeout)
    yield device
    if not twister_config.build_only:
        device.disconnect()
        device.stop()

import logging
from typing import Generator, Type

import pytest

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.device.device_abstract import DeviceAbstract
from twister2.device.factory import DeviceFactory
from twister2.exceptions import TwisterConfigurationException
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
    device = device_class(
        twister_config=twister_config,
        hardware_map=twister_config.get_hardware_map(platform=spec.platform)
    )

    if not twister_config.build_only:
        device.connect()
        device.flash(build_dir=build_dir, timeout=spec.timeout)
        device.run(build_dir=build_dir, timeout=spec.timeout)
    yield device
    if not twister_config.build_only:
        device.disconnect()
        device.stop()

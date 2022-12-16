from pathlib import Path

import pytest

from twister2.platform_specification import PlatformSpecification
from twister2.twister_config import TwisterConfig

pytest_plugins = ['pytester']


@pytest.fixture
def resources(request: pytest.FixtureRequest) -> Path:
    """Return path to `data` folder"""
    return Path(request.module.__file__).parent.joinpath('data')


@pytest.fixture(scope='function')
def platform() -> PlatformSpecification:
    """Return instance of PlatformSpecification"""
    return PlatformSpecification(identifier='platform_xyz')


@pytest.fixture(scope='function')
def twister_config(platform) -> TwisterConfig:
    """Return new instance of TwisterConfig"""
    return TwisterConfig(
        zephyr_base='dummy_path',
        default_platforms=[platform.identifier],
        platforms=[platform]
    )

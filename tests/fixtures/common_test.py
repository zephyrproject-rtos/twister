from unittest.mock import MagicMock

import pytest

from twister2.fixtures.common import SetupTestManager


@pytest.fixture
def request_mock():
    instance = MagicMock(pytest.FixtureRequest)
    return instance


@pytest.mark.parametrize(
    'build_only, device_testing, runnable, platform_type, expected',
    [
        (True, False, False, 'any', False),
        (False, True, False, 'any', False),
        (False, True, False, 'mcu', False),
        (False, False, True, 'mcu', False),
        (False, False, True, 'any', True),
    ]
)
def test_if_test_should_be_skipped(build_only, device_testing, runnable, platform_type, expected):
    result = SetupTestManager.should_be_executed(build_only, device_testing, runnable, platform_type)
    assert result.should_run == expected


@pytest.mark.parametrize(
    'spec_type, platform_type, platform_simulation, expected_device',
    [
        ('integration', 'qemu', 'qemu', 'qemu'),
        ('integration', 'native', 'native', 'native'),
        ('integration', 'sim', 'nsim', 'custom'),
        ('integration', 'mcu', 'na', 'hardware'),
    ]
)
def test_if_get_device_type_returns_proper_device(
    request_mock, spec_type, platform_type, platform_simulation, expected_device
):
    manager = SetupTestManager(request_mock)
    manager.specification.type = spec_type
    manager.platform.type = platform_type
    manager.platform.simulation = platform_simulation

    assert manager.get_device_type() == expected_device

import pytest

from twister2.fixtures.common import TestSetupManager


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
    result = TestSetupManager.should_be_executed(build_only, device_testing, runnable, platform_type)
    assert result.should_run == expected

import sys
from unittest import mock

import pytest

from twister2.device.hardware_adapter import HardwareAdapter
from twister2.device.hardware_map import HardwareMap
from twister2.twister_config import TwisterConfig


@pytest.fixture(name='device')
def fixture_adapter(resources) -> HardwareAdapter:
    return HardwareAdapter(
        TwisterConfig(zephyr_base=str(resources)),
        hardware_map=HardwareMap(
            id='test',
            product='product',
            platform='platform',
            runner='runner',
            connected=True
        )
    )


@mock.patch('twister2.device.hardware_adapter.shutil.which')
def test_if_get_command_returns_proper_string_1(patched_which, device) -> None:
    patched_which.return_value = 'west'
    command = device._get_command('src')
    assert isinstance(command, list)
    assert command == ['west', 'flash', '--skip-rebuild', '--build-dir', 'src', '--runner', 'runner']


@mock.patch('twister2.device.hardware_adapter.shutil.which')
def test_if_get_command_returns_proper_string_2(patched_which, device) -> None:
    patched_which.return_value = 'west'
    device.hardware_map.runner = 'pyocd'
    device.hardware_map.probe_id = 'p_id'
    command = device._get_command('src')
    assert isinstance(command, list)
    assert command == [
        'west', 'flash', '--skip-rebuild', '--build-dir', 'src', '--runner',  'pyocd', '--', '--board-id', 'p_id'
    ]


@mock.patch('twister2.device.hardware_adapter.shutil.which')
def test_if_get_command_returns_proper_string_3(patched_which, device) -> None:
    patched_which.return_value = 'west'
    device.hardware_map.runner = 'nrfjprog'
    device.hardware_map.probe_id = 'p_id'
    command = device._get_command('src')
    assert isinstance(command, list)
    assert command == [
        'west', 'flash', '--skip-rebuild', '--build-dir', 'src', '--runner',  'nrfjprog', '--', '--dev-id', 'p_id'
    ]


@mock.patch('twister2.device.hardware_adapter.shutil.which')
def test_if_get_command_returns_proper_string_4(patched_which, device) -> None:
    patched_which.return_value = 'west'
    device.hardware_map.runner = 'openocd'
    device.hardware_map.product = 'STM32 STLink'
    device.hardware_map.probe_id = 'p_id'
    command = device._get_command('src')
    assert isinstance(command, list)
    assert command == [
        'west', 'flash', '--skip-rebuild', '--build-dir', 'src', '--runner',  'openocd',
        '--', '--cmd-pre-init', 'hla_serial p_id'
    ]


@mock.patch('twister2.device.hardware_adapter.shutil.which')
def test_if_get_command_returns_proper_string_5(patched_which, device) -> None:
    patched_which.return_value = 'west'
    device.hardware_map.runner = 'openocd'
    device.hardware_map.product = 'EDBG CMSIS-DAP'
    device.hardware_map.probe_id = 'p_id'
    command = device._get_command('src')
    assert isinstance(command, list)
    assert command == [
        'west', 'flash', '--skip-rebuild', '--build-dir', 'src', '--runner',  'openocd',
        '--', '--cmd-pre-init', 'cmsis_dap_serial p_id'
    ]


@mock.patch('twister2.device.hardware_adapter.shutil.which')
def test_if_get_command_returns_proper_string_6(patched_which, device) -> None:
    patched_which.return_value = 'west'
    device.hardware_map.runner = 'jlink'
    device.hardware_map.probe_id = 'p_id'
    command = device._get_command('src')
    assert isinstance(command, list)
    assert command == [
        'west', 'flash', '--skip-rebuild', '--build-dir', 'src', '--runner',  'jlink',
        '--tool-opt=-SelectEmuBySN p_id'
    ]


@mock.patch('twister2.device.hardware_adapter.shutil.which')
def test_if_get_command_returns_proper_string_7(patched_which, device) -> None:
    patched_which.return_value = 'west'
    device.hardware_map.runner = 'stm32cubeprogrammer'
    device.hardware_map.probe_id = 'p_id'
    command = device._get_command('src')
    assert isinstance(command, list)
    assert command == [
        'west', 'flash', '--skip-rebuild', '--build-dir', 'src', '--runner',  'stm32cubeprogrammer',
        '--tool-opt=sn=p_id'
    ]

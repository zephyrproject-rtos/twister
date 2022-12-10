import textwrap
from unittest import mock

import pytest
import yaml
from serial.tools.list_ports_common import ListPortInfo

from twister2.device.hardware_map import HardwareMap
from twister2.scripts import hardware_map


@pytest.fixture
def hm_list():
    return [
        HardwareMap(
            id='id1',
            product='product1',
            platform='platform1',
            runner='runner1',
            connected=True,
            serial='/dev/ttyACM0'
        ),
        HardwareMap(
            id='id2',
            product='product2',
            platform='platform2',
            runner='runner2',
            connected=True,
            serial='/dev/ttyACM0'
        )
    ]


def patched_comports():
    device1 = ListPortInfo('/dev/ttyACM0')
    device1.manufacturer = 'SEGGER'
    device1.serial_number = '001'
    device1.product = 'J-Link'

    device2 = ListPortInfo('/dev/ttyACM1')
    device2.manufacturer = 'ARM'
    device2.serial_number = '002'
    device2.product = 'Product-2'

    device3 = ListPortInfo('/dev/ttyACM3')
    device3.serial_number = '003'
    return [device1, device2, device3]


def patched_get_persistent_map():
    return {
        '/dev/ttyACM0': 'usb-SEGGER_J-Link_000683444357-if00',
        '/dev/ttyACM1': 'usb-SEGGER_J-Link_000683444823-if00'
    }


@mock.patch('serial.tools.list_ports.comports', patched_comports)
def test_if_scan_hardwares_returns_not_empty_list():
    hardwares_list = hardware_map.scan()
    assert len(hardwares_list) == 2
    assert {hd.id for hd in hardwares_list} == {'001', '002'}
    assert {hd.product for hd in hardwares_list} == {'J-Link', 'Product-2'}
    assert {hd.serial for hd in hardwares_list} == {'/dev/ttyACM0', '/dev/ttyACM1'}
    assert {hd.platform for hd in hardwares_list} == {'unknown'}
    assert {hd.connected for hd in hardwares_list} == {True}
    assert {hd.runner for hd in hardwares_list} == {'unknown', 'jlink'}


@mock.patch('serial.tools.list_ports.comports', patched_comports)
@mock.patch('twister2.scripts.hardware_map.get_persistent_map', patched_get_persistent_map)
def test_if_scan_hardwares_returns_not_empty_list_for_persistent_true():
    hardwares_list = hardware_map.scan(persistent=True)
    assert len(hardwares_list) == 2
    assert {hd.id for hd in hardwares_list} == {'001', '002'}
    assert {hd.product for hd in hardwares_list} == {'J-Link', 'Product-2'}
    assert {hd.serial for hd in hardwares_list} == {
        'usb-SEGGER_J-Link_000683444357-if00',
        'usb-SEGGER_J-Link_000683444823-if00'
    }
    assert {hd.platform for hd in hardwares_list} == {'unknown'}
    assert {hd.connected for hd in hardwares_list} == {True}
    assert {hd.runner for hd in hardwares_list} == {'unknown', 'jlink'}


def test_if_filtering_hardware_map_returns_propper_items(hm_list):
    filtered = list(hardware_map.filter_hardware_map(hm_list))
    assert len(filtered) == 2


def test_if_filtering_hardware_map_by_platform_returns_propper_items(hm_list):
    filtered = list(hardware_map.filter_hardware_map(hm_list, filtered=['platform1']))
    assert len(filtered) == 1


def test_if_filtering_hardware_map_by_connected_only_returns_propper_items(hm_list):
    hm_list[0].connected = False
    filtered = list(hardware_map.filter_hardware_map(hm_list, connected_only=True))
    assert len(filtered) == 1


def test_if_hardware_map_can_be_saved_to_file(tmp_path, hm_list):
    hm_file = tmp_path / 'hardware-map.yaml'
    hardware_map.write_to_file(hm_file, hm_list)

    data = yaml.safe_load(hm_file.read_text())
    assert len(data) == 2
    assert {hw['id'] for hw in data} == {'id1', 'id2'}
    assert {hw['connected'] for hw in data} == {True}


def test_if_hardware_map_can_be_saved_to_file_which_already_exists(tmp_path, hm_list):
    content = textwrap.dedent("""
        - available: false
          baud: '115200'
          connected: true
          fixtures: []
          id: id3
          notes: ''
          platform: unknown
          post_flash_script: ''
          post_script: ''
          pre_script: ''
          probe_id: ''
          product: J-Link
          runner: jlink
          serial: /dev/ttyACM3
    """)
    hm_file = tmp_path / 'hardware-map.yaml'
    hm_file.write_text(content)

    hardware_map.write_to_file(hm_file, hm_list)

    data = yaml.safe_load(hm_file.read_text())
    assert len(data) == 3
    assert {hw['id'] for hw in data} == {'id1', 'id2', 'id3'}
    assert {hw['id']: hw['connected'] for hw in data} == {'id1': True, 'id2': True, 'id3': False}

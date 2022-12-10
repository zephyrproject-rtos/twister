from __future__ import annotations

import logging
import os
import platform
import re
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Iterable

import yaml
from serial.tools import list_ports
from tabulate import tabulate

from twister2.device.hardware_map import HardwareMap

if TYPE_CHECKING:
    from serial.tools.list_ports_common import ListPortInfo


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

MANUFACTURER: list[str] = [
    'ARM',
    'SEGGER',
    'MBED',
    'STMicroelectronics',
    'Atmel Corp.',
    'Texas Instruments',
    'Silicon Labs',
    'NXP Semiconductors',
    'Microchip Technology Inc.',
    'FTDI',
    'Digilent'
]


RUNNER_MAPPING: dict[str, list[str]] = {
    'pyocd': [
        'DAPLink CMSIS-DAP',
        'MBED CMSIS-DAP'
    ],
    'jlink': [
        'J-Link',
        'J-Link OB'
    ],
    'openocd': [
        'STM32 STLink', '^XDS110.*', 'STLINK-V3'
    ],
    'dediprog': [
        'TTL232R-3V3',
        'MCP2200 USB Serial Port Emulator'
    ]
}


def get_persistent_map() -> dict[str, str]:
    by_id = Path('/dev/serial/by-id')

    def readlink(link):
        return str((by_id / link).resolve())

    persistent_map = {
        readlink(link): str(link)
        for link in by_id.iterdir()
    }
    return persistent_map


def scan(persistent: bool = False) -> list[HardwareMap]:
    """Scan for connected devices and generate hardware map."""
    hardware_map_list = []

    if persistent and platform.system() == 'Linux':
        persistent_map = get_persistent_map()
    else:
        persistent_map = {}

    logger.info('Scanning connected hardware...')
    device_names: list[ListPortInfo] = list_ports.comports()

    for device in device_names:
        logger.info('Found device: %s', device)
        if device.manufacturer not in MANUFACTURER:
            logger.warning('Unsupported device (%s): %s' % (device.manufacturer, device))
            continue

        # TI XDS110 can have multiple serial devices for a single board
        # assume endpoint 0 is the serial, skip all others
        if (
            device.manufacturer == 'Texas Instruments'
            and device.location is not None
            and not device.location.endswith('0')
        ):
            continue

        hardware_map: HardwareMap = HardwareMap(
            platform='unknown',
            id=device.serial_number or '',
            serial=persistent_map.get(device.device, device.device),
            product=device.product or '',
            runner='unknown',
            connected=True
        )

        # find runner for the device
        if device.product is not None:
            for runner, products in RUNNER_MAPPING.items():
                if device.product in products:
                    hardware_map.runner = runner
                    continue
                # Try regex matching
                if any(re.match(product, device.product) for product in products):
                    hardware_map.runner = runner

        hardware_map_list.append(hardware_map)

    return hardware_map_list


def write_to_file(filename: str | Path, hardware_map_list: list[HardwareMap]) -> None:
    """Save hardware map to file."""
    new_hardware_map_list = hardware_map_list
    merged_hardware_map_list = []

    # update existing hardware map
    if os.path.exists(filename):
        old_hardware_map_list = HardwareMap.read_from_file(filename)
        for hardware in old_hardware_map_list:
            hardware.connected = False
            hardware.serial = ''

        for new_hardware in new_hardware_map_list:
            for old_hardware in old_hardware_map_list:
                if old_hardware.id == new_hardware.id and old_hardware.product == new_hardware.product:
                    old_hardware.serial = new_hardware.serial
                    old_hardware.connected = True
                    break
            else:  # for ... else
                merged_hardware_map_list.append(new_hardware)
        merged_hardware_map_list.extend(old_hardware_map_list)
    else:
        merged_hardware_map_list = new_hardware_map_list

    # save hardware map to YAML file
    with open(filename, 'w', encoding='UTF-8') as file:
        hardware_map_list_as_dict = [device.asdict() for device in merged_hardware_map_list]
        yaml.dump(hardware_map_list_as_dict, file, Dumper=yaml.Dumper, default_flow_style=False)
        logger.info('Saved as %s', filename)


def filter_hardware_map(
    hardware_map_list: Iterable[HardwareMap],
    filtered: list[str] | None = None,
    connected_only: bool = False
) -> Generator[HardwareMap, None, None]:
    """
    Return filtered list of hardware map.

    :param hardware_map: list of hardware map
    :param fitered: list of platform to display
    :param connected_only: display only connected devices
    :return: filtered hardware map list
    """

    hardware_map_generator = (
        hardware for hardware in hardware_map_list
    )

    if filtered:
        hardware_map_generator = (
            hardware for hardware in hardware_map_generator
            if hardware.platform in filtered
        )

    if connected_only:
        hardware_map_generator = (
            hardware for hardware in hardware_map_generator
            if hardware.connected is True
        )

    return hardware_map_generator


def print_hardware_map(hardware_map_list: Iterable[HardwareMap]) -> None:
    """
    Print hardware devices in pretty way.

    :param hardware_map: list of hardware map
    """
    headers = ['platform', 'id', 'serial']
    table = (
        (hardware.platform, hardware.id, hardware.serial)
        for hardware in hardware_map_list
    )

    print()
    print(tabulate(table, headers=headers, tablefmt='github'))

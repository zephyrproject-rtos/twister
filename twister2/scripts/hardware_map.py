from __future__ import annotations

import logging
import os
import platform
import re
from pathlib import Path

import yaml
from serial.tools import list_ports

from twister2.device.hardware_map import HardwareMap

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

MANUFACTURER = [
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

RUNNER_MAPPING = {
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


def scan(persistent: bool = False) -> list[HardwareMap]:
    """Scan for connected devices and generate hardware map."""
    hardware_map_list = []
    if persistent and platform.system() == 'Linux':

        by_id = Path('/dev/serial/by-id')

        def readlink(link):
            return str((by_id / link).resolve())

        persistent_map = {
            readlink(link): str(link)
            for link in by_id.iterdir()
        }
    else:
        persistent_map = {}

    logger.info('Scanning connected hardware...')
    serial_devices = list_ports.comports()

    for device in serial_devices:
        logger.info('Found device: %s', device)
        if device.manufacturer in MANUFACTURER:

            # TI XDS110 can have multiple serial devices for a single board
            # assume endpoint 0 is the serial, skip all others
            if device.manufacturer == 'Texas Instruments' and not device.location.endswith('0'):
                continue
            hardware_map: HardwareMap = HardwareMap(
                platform='unknown',
                id=device.serial_number,
                serial=persistent_map.get(device.device, device.device),
                product=device.product,
                runner='unknown',
                connected=True
            )

            for runner in RUNNER_MAPPING.keys():
                products = RUNNER_MAPPING.get(runner)
                if device.product in products:
                    hardware_map.runner = runner
                    continue
                # Try regex matching
                for product in products:
                    if re.match(product, device.product):
                        hardware_map.runner = runner

            hardware_map.connected = True
            hardware_map.lock = None
            hardware_map_list.append(hardware_map)
        else:
            logger.warning('Unsupported device (%s): %s' % (device.manufacturer, device))

    return hardware_map_list


def write_to_file(filename: str | Path, hardware_map_list: list[HardwareMap]) -> None:
    """Save hardware map to file."""
    new_hardware_map = hardware_map_list.copy()

    # update existing hardware map
    if os.path.exists(filename):
        old_hardware_map_list = HardwareMap.read_from_file(filename)
        for hardware in old_hardware_map_list:
            hardware.connected = False
            hardware.serial = None

        while new_hardware_map:
            new_hardware = new_hardware_map.pop()
            for old_hardware in reversed(old_hardware_map_list):
                if old_hardware.id == new_hardware.id and old_hardware.product == new_hardware.product:
                    old_hardware.serial = new_hardware.serial
                    old_hardware.connected = True
                    break
            else:
                old_hardware_map_list.append(new_hardware)

        new_hardware_map = old_hardware_map_list

    with open(filename, 'w', encoding='UTF-8') as file:
        hardware_map_list_as_dict = [device.asdict() for device in new_hardware_map]
        yaml.dump(hardware_map_list_as_dict, file, Dumper=yaml.Dumper, default_flow_style=False)
        logger.info('Saved as %s', filename)


def print_hardware_map(
    hardware_map_list: list[HardwareMap],
    filtered: list[str] | None = None,
    connected_only: bool = False,
    detected: bool = False
) -> None:
    """Print hardware devices in pretty way."""
    # TODO: needs some work
    if connected_only:
        hardware_map_list = [
            hardware for hardware in hardware_map_list
            if hardware.connected is True
        ]

    print()
    print(f'| {"Platform":20} | {"ID":>20} | {"Serial devices":20} |')
    print(f'|{"-" * 22}|{"-" * 22}|{"-" * 22}|')
    for hardware in hardware_map_list:
        print(f'| {hardware.platform:20} | {hardware.id:20} | {hardware.serial or "":20} |')
    print()

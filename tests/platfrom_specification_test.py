from __future__ import annotations

import textwrap
from pathlib import Path
from unittest import mock

import pytest

from twister2.exceptions import TwisterConfigurationException
from twister2.platform_specification import (
    PlatformSpecification,
    discover_platform_revisions,
    discover_platforms,
    search_platforms,
    validate_platforms_list,
)


def test_if_platform_specification_can_be_load_from_yaml_file(resources):
    board_file = resources.joinpath('boards', 'arm', 'mps2_an521', 'mps2_an521_remote.yaml')
    platform = PlatformSpecification.load_from_yaml(board_file)
    assert isinstance(platform, PlatformSpecification)
    assert isinstance(platform.testing.default, bool)
    assert isinstance(platform.ram, int)
    assert platform.ram == 4096
    assert platform.identifier == 'mps2_an521_remote'
    assert isinstance(platform.toolchain, list)
    assert isinstance(platform.supported, set)
    assert platform.supported == {'clock_controller', 'eeprom', 'gpio', 'i2c', 'pinmux', 'serial'}


def test_if_discover_platforms_discovers_all_defined_platforms_in_directory(resources: Path):
    boards_dir = resources / 'boards'
    platforms = list(discover_platforms(boards_dir))
    assert len(platforms) == 7
    assert {platform.identifier for platform in platforms} == {
        'qemu_cortex_m3', 'mps2_an521_remote', 'native_posix', 'altera_max10',
        'stm32f411e_disco', 'stm32f411e_disco@B', 'stm32f411e_disco@D'
    }


def test_if_search_platforms_discovers_all_defined_platforms(resources: Path):
    zephyr_base = str(resources)
    platforms = search_platforms(zephyr_base=zephyr_base)
    assert len(platforms) == 7
    assert {platform.identifier for platform in platforms} == {
        'qemu_cortex_m3', 'mps2_an521_remote', 'native_posix', 'altera_max10',
        'stm32f411e_disco', 'stm32f411e_disco@B', 'stm32f411e_disco@D'
    }


def test_if_validate_platforms_list_raises_exception_for_duplicated_platform():
    platforms = [
        PlatformSpecification('native_posix'),
        PlatformSpecification('qemu_cortex_m3'),
        PlatformSpecification('native_posix'),
    ]
    with pytest.raises(Exception, match='There are duplicated platforms: native_posix'):  # it raises Exit(Exception)
        validate_platforms_list(platforms)


def test_if_validation_error_is_raised_for_incorrect_platform_schema(tmp_path):
    content = textwrap.dedent("""\
        identifier: native_posix
        name: Native 32-bit POSIX port
        type: foobar
        arch: posix
        ram: 65536
        flash: 65536
        toolchain:
          - host
          - llvm
        supported:
          - spi
          - gpio
        testing:
          default: true
    """)
    board_file: Path = tmp_path / 'native_posix.yaml'
    board_file.write_text(content)
    with pytest.raises(TwisterConfigurationException, match='Cannot create PlatformSpecification from yaml data'):
        PlatformSpecification.load_from_yaml(board_file)


def test_if_discover_platform_revisions_returns_expected_platforms():
    platform = PlatformSpecification('qemu_x86_tiny')
    files = [
        'qemu_x86_tiny_0.conf',  # valid
        'qemu_x86_tiny_012.conf',  # valid
        'qemu_x86_tiny_0_1.conf',  # valid
        'qemu_x86_tiny_9_9.conf',  # valid
        'qemu_x86_tiny_1_2_3.conf',  # valid
        'qemu_x86_tiny_0_1_2_5.conf',
        'qemu_x86_tiny_123.conf',  # valid
        'qemu_x86_tiny_123_1.conf',  # valid
        'qemu_x86_tiny_D.conf',  # valid
        'qemu_x86_tiny_D_123.conf',
        'qemu_x86_tiny_ABC.conf',
        'qemu_x86_tiny.yaml',
        'qemu_x86_tiny.ld',
        'foo.py',
        'foo.conf',
        'dummy'
    ]
    with mock.patch('os.listdir') as patched_listdir:
        patched_listdir.return_value = files
        platforms = list(discover_platform_revisions(platform=platform, directory=Path('any')))
    assert len(platforms) == 8
    assert {p.identifier for p in platforms} == {
        'qemu_x86_tiny@0',
        'qemu_x86_tiny@012',
        'qemu_x86_tiny@0.1',
        'qemu_x86_tiny@9.9',
        'qemu_x86_tiny@1.2.3',
        'qemu_x86_tiny@123',
        'qemu_x86_tiny@123.1',
        'qemu_x86_tiny@D',
    }

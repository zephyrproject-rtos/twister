from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from twister2.exceptions import TwisterConfigurationException
from twister2.platform_specification import (
    PlatformSpecification,
    discover_platforms,
    search_platforms,
    validate_platforms_list,
)


def test_if_platform_specification_can_be_load_from_yaml_file(resources):
    board_file = resources.joinpath('boards', 'arm', 'mps2_an521', 'mps2_an521_remote.yaml')
    platform = PlatformSpecification.load_from_yaml(board_file)
    assert isinstance(platform, PlatformSpecification)
    assert isinstance(platform.default, bool)
    assert isinstance(platform.ram, int)
    assert platform.ram == 4096
    assert platform.identifier == 'mps2_an521_remote'
    assert isinstance(platform.toolchain, list)
    assert isinstance(platform.supported, set)
    assert platform.supported == {'clock_controller', 'eeprom', 'gpio', 'i2c', 'pinmux', 'serial'}


def test_if_discover_platforms_discovers_all_defined_platforms_in_directory(resources: Path):
    boards_dir = resources / 'boards'
    platforms = list(discover_platforms(boards_dir))
    assert len(platforms) == 3
    assert {platform.identifier for platform in platforms} == {'qemu_cortex_m3', 'mps2_an521_remote', 'native_posix'}


def test_if_search_platforms_discovers_all_defined_platforms(resources: Path):
    zephyr_base = str(resources)
    platforms = search_platforms(zephyr_base=zephyr_base)
    assert len(platforms) == 3
    assert {platform.identifier for platform in platforms} == {'qemu_cortex_m3', 'mps2_an521_remote', 'native_posix'}


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

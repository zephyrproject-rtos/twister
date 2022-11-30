from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

import pytest
import yaml
from marshmallow import Schema, fields, validate

from twister2.exceptions import TwisterConfigurationException
from twister2.helper import string_to_set

logger = logging.getLogger(__name__)


@dataclass
class Testing:
    default: bool = False
    only_tags: set[str] = field(default_factory=set)
    ignore_tags: set[str] = field(default_factory=set)
    timeout_multiplier: int = None

    def __post_init__(self):
        self.only_tags = string_to_set(self.only_tags)
        self.ignore_tags = string_to_set(self.ignore_tags)


@dataclass
class PlatformSpecification:
    """Store platform configuration."""
    identifier: str = ''  # platform name
    name: str = ''  # long name
    twister: bool = True
    ram: int = 128  # in kilobytes
    flash: int = 512  # in kilobytes
    ignore_tags: list[str] = field(default_factory=list)
    only_tags: list[str] = field(default_factory=list)
    default: bool = False
    supported: set = field(default_factory=set)
    arch: str = ''
    type: str = 'na'  # mcu, qemu, sim, unit, native
    simulation: str = 'na'  # qemu, simics, xt-sim, renode, nsim, mdb-nsim, tsim, armfvp
    simulation_exec: str = 'na'
    toolchain: list[str] = field(default_factory=list)  # supported_toolchains
    env: list[str] = field(default_factory=list)
    env_satisfied: bool = True
    filter_data: dict = field(default_factory=dict)
    testing: Testing = field(default_factory=Testing)

    def __post_init__(self):
        self.supported = set(self.supported)
        if isinstance(self.testing, dict):
            self.testing = Testing(**self.testing)

    @classmethod
    def load_from_yaml(cls, filename: str | Path) -> PlatformSpecification:
        """Load platform from yaml file."""
        with open(filename, 'r', encoding='UTF-8') as file:
            data: dict = yaml.safe_load(file)
        try:
            data = PlatformSchema().load(data)
            return cls.from_dict(data)
        except Exception as e:
            logger.exception('Cannot create PlatformSpecification from yaml data: %s', data)
            raise TwisterConfigurationException('Cannot create PlatformSpecification from yaml data') from e

    @classmethod
    def from_dict(cls, data: dict) -> PlatformSpecification:
        if testing := data.pop('testing', None):
            testing = Testing(**testing)
            data['testing'] = testing
        return PlatformSpecification(**data)


# Using marshmallow schema definition for validation of data read from yaml
_validate_type = validate.OneOf(
    ['mcu', 'qemu', 'sim', 'unit', 'native']
)
_validate_simulation = validate.OneOf(
    ['qemu', 'simics', 'xt-sim', 'renode', 'nsim', 'mdb-nsim', 'tsim', 'armfvp', 'native']
)


class TestingSchema(Schema):
    default = fields.Bool()
    only_tags = fields.List(fields.Str)
    ignore_tags = fields.List(fields.Str)
    timeout_multiplier = fields.Int()


class PlatformSchema(Schema):
    identifier = fields.Str()
    name = fields.Str()
    twister = fields.Bool()
    ram = fields.Int()
    flash = fields.Int()
    ignore_tags = fields.List(fields.Str())
    only_tags = fields.List(fields.Str())
    default = fields.Bool()
    supported = fields.List(fields.Str())
    arch = fields.Str()
    type = fields.Str(validate=_validate_type)
    simulation = fields.Str(validate=_validate_simulation)
    simulation_exec = fields.Str()
    toolchain = fields.List(fields.Str())
    env = fields.List(fields.Str())
    env_satisfied = fields.Bool()
    filter_data = fields.Dict()
    testing = fields.Nested(TestingSchema())


def discover_platforms(directory: Path) -> Generator[PlatformSpecification, None, None]:
    """Return platforms from given directory"""
    for file in directory.glob('*/*/*.yaml'):
        try:
            yield PlatformSpecification.load_from_yaml(str(file))
        except Exception as e:
            logger.exception('Cannot read platform definition from yaml: %e', e)
            raise


def validate_platforms_list(platforms: list[PlatformSpecification]) -> None:
    """Validate platforms."""
    # varify duplications
    duplicated: list[str] = []
    platforms_list: list[str] = []
    for platform in platforms:
        if platform.identifier in platforms_list:
            duplicated.append(platform.identifier)
        else:
            platforms_list.append(platform.identifier)
    if len(duplicated) != 0:
        pytest.exit(f'There are duplicated platforms: {", ".join(duplicated)}')


def search_platforms(zephyr_base: str, board_root: str = None) -> list[PlatformSpecification]:
    """Return list of platforms."""
    board_root_list = [
        f'{zephyr_base}/boards',
        f'{zephyr_base}/scripts/pylib/twister/boards',
    ]
    if board_root:
        board_root_list.extend(board_root)

    logger.debug('BOARD_ROOT_LIST: %s', board_root_list)

    platforms: list[PlatformSpecification] = []
    for directory in board_root_list:
        logger.info('Reading platform configuration files under %s', directory)
        for platform_config in discover_platforms(Path(directory)):
            logger.debug('Found platform: %s', platform_config.identifier)
            platforms.append(platform_config)
    validate_platforms_list(platforms)
    return platforms

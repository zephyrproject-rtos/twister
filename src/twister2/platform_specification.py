from __future__ import annotations

import copy
import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from os import getenv
from pathlib import Path
from typing import Generator

import pytest
from marshmallow import Schema, fields, validate

from twister2.exceptions import TwisterConfigurationException
from twister2.helper import safe_load_yaml, string_to_set

logger = logging.getLogger(__name__)


@dataclass
class Testing:
    default: bool = False
    only_tags: set[str] = field(default_factory=set)
    ignore_tags: set[str] = field(default_factory=set)
    binaries: set[str] = field(default_factory=set)
    timeout_multiplier: float = 1

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
        for env in self.env:
            if not getenv(env, None):
                self.env_satisfied = False
        if isinstance(self.testing, dict):
            self.testing = Testing(**self.testing)

    @classmethod
    def load_from_yaml(cls, filename: str | Path) -> PlatformSpecification:
        """Load platform from yaml file."""
        data: dict = safe_load_yaml(Path(filename))
        try:
            data = PlatformSchema().load(data)
            return cls.from_dict(data)
        except Exception as e:
            logger.error('Cannot create PlatformSpecification from yaml data: %s', data)
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
    binaries = fields.List(fields.Str)
    timeout_multiplier = fields.Float()


class PlatformSchema(Schema):
    identifier = fields.Str()
    name = fields.Str()
    twister = fields.Bool()
    ram = fields.Int()
    flash = fields.Int()
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
    for spec_file in directory.glob('*/*/*.yaml'):
        try:
            platform = PlatformSpecification.load_from_yaml(str(spec_file))
        except Exception as e:
            logger.exception('Cannot read platform definition from yaml: %s', e)
            raise
        yield platform
        if '@' not in platform.identifier:
            yield from discover_platform_revisions(platform, spec_file.parent)


def discover_platform_revisions(
    platform: PlatformSpecification, directory: Path
) -> Generator[PlatformSpecification, None, None]:
    """
    Return all revisions for platform specification in the directory.

    :param platform: platform specification
    :param directory: directory to search revision in
    :return: all revisions for given platform
    """
    # Revision pattern is created according to the documentation
    # https://docs.zephyrproject.org/latest/hardware/porting/board_porting.html#multiple-board-revisions
    revision_pattern: str = '([A-Z]|[0-9]+_?[0-9]?_?[0-9]*)'
    files_list: list[str] = os.listdir(directory)
    for file in files_list:
        # Need to make sure the revision matches
        # the permitted patterns as described in
        # cmake/modules/extensions.cmake.
        pattern_to_match = r'{}_(?P<revision>{})\.conf'.format(platform.identifier, revision_pattern)
        if match := re.match(pattern_to_match, file):
            revision: str = match.group('revision')
            if f'{platform.identifier}_{revision}.yaml' not in files_list:
                platform_revision = copy.deepcopy(platform)
                revision = revision.replace('_', '.')
                platform_revision.identifier = f'{platform.identifier}@{revision}'
                platform_revision.testing.default = False
                yield platform_revision


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


def search_platforms(
    zephyr_base: str,
    board_root: str | None = None,
    default_only: bool = False
) -> list[PlatformSpecification]:
    """
    Return list of platforms.

    :param zephyr_base: path to Zephyr directory
    :param board_root: path to additional Boards directory
    :param default_only: return only default platforms
    :return: list of platform specifications
    """
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
            if default_only and platform_config.testing.default is False:
                logger.debug('Skip for not default platform: %s', platform_config.identifier)
                continue
            logger.debug('Found platform: %s', platform_config.identifier)
            platforms.append(platform_config)
    validate_platforms_list(platforms)
    return platforms


def is_simulation_platform_available(simulation_exec: str | None) -> bool:
    """Check if simulation program is available on the test setup"""
    if simulation_exec and simulation_exec != 'na':
        if shutil.which(simulation_exec) is None:
            logger.debug(f'{simulation_exec} not found.')
            return False
    return True

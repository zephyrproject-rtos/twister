from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import pytest

from twister2.device.hardware_map import HardwareMap
from twister2.environment.environment import get_toolchain_version
from twister2.exceptions import TwisterConfigurationException
from twister2.platform_specification import (
    PlatformSpecification,
    is_simulation_platform_available,
)

logger = logging.getLogger(__name__)


@dataclass
class TwisterConfig:
    """Store twister configuration to have easy access in test."""
    zephyr_base: str
    output_dir: str = 'twister-out'
    board_root: list = field(default_factory=list)
    build_only: bool = False
    selected_platforms: list[str] = field(default_factory=list, repr=False)
    platforms: list[PlatformSpecification] = field(default_factory=list, repr=False)
    hardware_map_list: list[HardwareMap] = field(default_factory=list, repr=False)
    device_testing: bool = False
    fixtures: list[str] = field(default_factory=list, repr=False)
    extra_args_cli: list = field(default_factory=list)
    overflow_as_errors: bool = False
    integration_mode: bool = False
    emulation_only: bool = False
    architectures: list[str] = field(default_factory=list, repr=False)
    # platform filter provided by user via --platform argument in CLI or via hardware map file
    user_platform_filter: list[str] = field(default_factory=list, repr=False)
    used_toolchain_version: str = ''

    def __post_init__(self):
        self.verify_platforms_existence(self.selected_platforms)

    @classmethod
    def create(cls, config: pytest.Config) -> TwisterConfig:
        """Create new instance from pytest.Config."""
        zephyr_base: str = (
            config.option.zephyr_base
            or config.getini('zephyr_base')
            or os.environ.get('ZEPHYR_BASE', '')
        )
        build_only: bool = config.option.build_only
        board_root: list[str] = config.option.board_root or config.getini('board_root')
        platforms: list[PlatformSpecification] = config._platforms  # type: ignore
        output_dir: str = config.option.output_dir
        hardware_map_file: str = config.option.hardware_map
        device_testing: bool = config.option.device_testing
        fixtures: list[str] = config.option.fixtures
        extra_args_cli: list[str] = config.getoption('--extra-args')
        overflow_as_errors: bool = config.option.overflow_as_errors
        integration_mode: bool = config.option.integration
        emulation_only: bool = config.option.emulation_only
        architectures: list[str] = config.option.arch

        hardware_map_list: list[HardwareMap] = []
        if hardware_map_file:
            hardware_map_list = HardwareMap.read_from_file(filename=hardware_map_file)
            if not config.option.platform:
                config.option.platform = [p.platform for p in hardware_map_list if p.connected]

        if config.option.all:
            # When --all used, any --platform arguments ignored
            config.option.platform = []

        user_platform_filter: list[str] = config.option.platform

        selected_platforms = _get_selected_platforms(config)

        used_toolchain_version = get_toolchain_version(output_dir, zephyr_base)

        data: dict[str, Any] = dict(
            zephyr_base=zephyr_base,
            build_only=build_only,
            platforms=platforms,
            selected_platforms=selected_platforms,
            board_root=board_root,
            output_dir=output_dir,
            hardware_map_list=hardware_map_list,
            device_testing=device_testing,
            fixtures=fixtures,
            extra_args_cli=extra_args_cli,
            overflow_as_errors=overflow_as_errors,
            integration_mode=integration_mode,
            emulation_only=emulation_only,
            architectures=architectures,
            user_platform_filter=user_platform_filter,
            used_toolchain_version=used_toolchain_version,
        )
        return cls(**data)

    def asdict(self) -> dict:
        """Return dictionary which can be serialized as Json."""
        return dict(
            build_only=self.build_only,
            selected_platforms=self.selected_platforms,
            board_root=self.board_root,
            output_dir=self.output_dir,
        )

    def get_hardware_map(self, platform: str) -> HardwareMap | None:
        """
        Return hardware map matching platform and being connected.

        :param platform: platform name
        :return: hardware map or None
        """
        hardware_map_iter = (
            hardware for hardware in self.hardware_map_list
            if hardware.platform == platform
            if hardware.connected is True
        )
        return next(hardware_map_iter, None)

    def get_platform(self, name: str) -> PlatformSpecification:
        for platform in self.platforms:
            if platform.identifier == name:
                return platform
        raise KeyError(f'There is not platform with identifier: {name}')

    def verify_platforms_existence(self, platform_names_to_verify: list[str]):
        """Verify if platform names are correct, if not - raise exception"""
        platform_names = [p.identifier for p in self.platforms]
        for platform in platform_names_to_verify:
            if platform not in platform_names:
                msg = f'Unrecognized platform - {platform}.'
                logger.error(msg)
                raise TwisterConfigurationException(msg)


def _get_selected_platforms(config: pytest.Config) -> list[str]:
    """Return list of selected platforms"""
    platforms: list[PlatformSpecification] = config._platforms  # type: ignore
    emulation_only: bool = config.option.emulation_only
    architectures: list[str] = config.option.arch
    all_filter: bool = config.option.all
    platform_filter: list[str] = config.option.platform

    selected_platforms: list[str] = []
    if platform_filter:
        selected_platforms = list(set(platform_filter))
    elif emulation_only:
        selected_platforms = [
            platform.identifier for platform in platforms
            if platform.simulation != 'na'
        ]
    elif architectures:
        if all_filter:
            selected_platforms = [
                platform.identifier for platform in platforms
                if platform.arch in architectures
            ]
        else:
            selected_platforms = [
                platform.identifier for platform in platforms
                if platform.testing.default and platform.arch in architectures
            ]
    elif all_filter:
        selected_platforms = [
            platform.identifier for platform in platforms
        ]
    else:
        for platform in platforms:
            if not platform.testing.default:
                continue
            # default platforms that can't be run are dropped from the list of
            # the default platforms list. Default platforms should always be runnable
            if platform.simulation \
               and not is_simulation_platform_available(platform.simulation_exec):
                continue
            selected_platforms.append(platform.identifier)

    return selected_platforms

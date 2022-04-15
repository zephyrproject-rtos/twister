from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import pytest

from twister2.device.hardware_map import HardwareMap
from twister2.platform_specification import PlatformSpecification

logger = logging.getLogger(__name__)


@dataclass
class TwisterConfig:
    """Store twister configuration to have easy access in test."""
    zephyr_base: str
    output_dir: str = 'twister-out'
    board_root: list = field(default_factory=list)
    build_only: bool = False
    default_platforms: list[str] = field(default_factory=list, repr=False)
    platforms: list[PlatformSpecification] = field(default_factory=list, repr=False)
    hardware_map_list: list[HardwareMap] = field(default_factory=list, repr=False)
    device_testing: bool = False

    @classmethod
    def create(cls, config: pytest.Config) -> TwisterConfig:
        """Create new instance from pytest.Config."""
        zephyr_base: str = (
                config.getoption('zephyr_base')
                or config.getini('zephyr_base')
                or os.environ.get('ZEPHYR_BASE')
        )
        build_only: bool = config.getoption('--build-only')
        default_platforms: list[str] = config.getoption('--platform')
        board_root: list[str] = config.getoption('--board-root')
        platforms: list[PlatformSpecification] = config._platforms
        output_dir: str = config.getoption('--outdir')
        hardware_map_file: str = config.getoption('--hardware-map')
        device_testing: bool = config.getoption('--device-testing')

        hardware_map_list: list[HardwareMap] = []
        if hardware_map_file:
            hardware_map_list = HardwareMap.read_from_file(filename=hardware_map_file)

        if not default_platforms:
            default_platforms = [
                platform.identifier for platform in platforms
                if platform.testing.default
            ]
        else:
            default_platforms = list(set(default_platforms))  # remove duplicates

        data: dict[str, Any] = dict(
            zephyr_base=zephyr_base,
            build_only=build_only,
            platforms=platforms,
            default_platforms=default_platforms,
            board_root=board_root,
            output_dir=output_dir,
            hardware_map_list=hardware_map_list,
            device_testing=device_testing,
        )
        return cls(**data)

    def asdict(self) -> dict:
        """Return dictionary which can be serialized as Json."""
        return dict(
            build_only=self.build_only,
            default_platforms=self.default_platforms,
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

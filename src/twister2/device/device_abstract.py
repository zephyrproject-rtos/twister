from __future__ import annotations

import abc
import logging
import os
from pathlib import Path
from typing import Generator

from twister2.device.hardware_map import HardwareMap
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


class DeviceAbstract(abc.ABC):
    """Class defines an interface for all devices."""

    def __init__(self, twister_config: TwisterConfig, hardware_map: HardwareMap | None = None, **kwargs) -> None:
        """
        :param twister_config: twister configuration
        :param hardware_map: device hardware map or None
        """
        self.twister_config: TwisterConfig = twister_config
        self.hardware_map: HardwareMap | None = hardware_map
        self.build_dir: Path | str = Path()
        self.timeout: float = 60.  # seconds

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    @property
    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env['ZEPHYR_BASE'] = str(self.twister_config.zephyr_base)
        return env

    @abc.abstractmethod
    def connect(self, timeout: float = 1) -> None:
        pass

    @abc.abstractmethod
    def disconnect(self) -> None:
        pass

    def flash(self, build_dir: str | Path, timeout: float = 60.0) -> None:
        """
        Flash and run code on a device.

        :param build_dir: build directory
        :param timeout: time out in seconds
        """

    @property
    @abc.abstractmethod
    def iter_stdout(self) -> Generator[str, None, None]:
        """Iterate stdout from a device."""

    def stop(self) -> None:
        """Stop device."""

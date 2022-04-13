from __future__ import annotations

import abc
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Generator

from twister2.device.hardware_map import HardwareMap
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


class DeviceAbstract(abc.ABC):

    def __init__(self, twister_config: TwisterConfig, hardware_map: HardwareMap | None = None, **kwargs):
        self.twister_config = twister_config
        self.lock: Lock = Lock()
        self.log_file: Path = Path('device.log')
        self.hardware_map: HardwareMap | None = hardware_map

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    @property
    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env['ZEPHYR_BASE'] = str(self.twister_config.zephyr_base)
        return env

    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def flash(self, build_dir: str | Path, timeout: float = 60.0) -> None:
        """
        Flash and run code on a device.

        :param build_dir: build directory
        :param timeout: time out in seconds
        """

    @property
    @abc.abstractmethod
    def out(self) -> Generator[str, None, None]:
        """Return output from a device."""

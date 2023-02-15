from __future__ import annotations

import abc
import logging
import os
from pathlib import Path
from typing import Generator

from twister2.log_files.log_file import LogFile, NullLogFile
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


class DeviceAbstract(abc.ABC):
    """Class defines an interface for all devices."""

    def __init__(self, twister_config: TwisterConfig, **kwargs) -> None:
        """
        :param twister_config: twister configuration
        """
        self.twister_config: TwisterConfig = twister_config
        self.handler_log_file: LogFile = NullLogFile.create()
        self.device_log_file: LogFile = NullLogFile.create()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    @property
    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env['ZEPHYR_BASE'] = str(self.twister_config.zephyr_base)
        return env

    @abc.abstractmethod
    def connect(self, timeout: float = 1) -> None:
        """Connect with the device (e.g. via UART)"""

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Close a connection with the device"""

    @abc.abstractmethod
    def generate_command(self, build_dir: Path | str) -> None:
        """
        Generate command which will be used during flashing or running device.

        :param build_dir: path to directory with built application
        """

    def flash_and_run(self, timeout: float = 60.0) -> None:
        """
        Flash and run application on a device.

        :param timeout: time out in seconds
        """

    @property
    @abc.abstractmethod
    def iter_stdout(self) -> Generator[str, None, None]:
        """Iterate stdout from a device."""

    @abc.abstractmethod
    def initialize_log_files(self, build_dir: str | Path):
        """
        Initialize file to store logs.

        :param build_dir: path to directory with built application
        """

    def stop(self) -> None:
        """Stop device."""

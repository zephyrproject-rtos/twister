from __future__ import annotations

import abc
import logging
import os
import threading
from pathlib import Path
from typing import Generator

from twister2.device.hardware_map import HardwareMap
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


class DeviceAbstract(threading.Thread, abc.ABC):

    def __init__(self, twister_config: TwisterConfig, hardware_map: HardwareMap | None = None, **kwargs) -> None:
        super().__init__(daemon=True)
        self.twister_config = twister_config
        self.hardware_map: HardwareMap | None = hardware_map
        self.build_dir: Path = Path()
        self._stop_job = False
        self.timeout: int = 60  # seconds
        self._exc: Exception | None = None  #: store any exception which appeared running this thread
        self._loop = None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    @property
    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env['ZEPHYR_BASE'] = str(self.twister_config.zephyr_base)
        return env

    @abc.abstractmethod
    def connect(self) -> None:
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
        logger.info('Flashing device')
        self.build_dir = build_dir
        self.timeout = timeout
        self.start()

    @property
    @abc.abstractmethod
    def out(self) -> Generator[str, None, None]:
        """Return output from a device."""

    def join(self, timeout: float = None) -> None:
        super().join(timeout=1)
        if not self._loop.is_closed:
            self._loop.close()
        # Since join() returns in caller thread
        # we re-raise the caught exception
        # if any was caught
        if self._exc:
            raise self._exc

    def stop(self) -> None:
        self._stop_job = True
        self.join()

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from enum import Enum
from pathlib import Path

from filelock import BaseFileLock, FileLock

from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.exceptions import TwisterBuildException

_TMP_DIR: str = tempfile.gettempdir()
BUILD_STATUS_FILE_NAME: str = 'twister_builder.json'
BUILD_LOCK_FILE_PATH: str = os.path.join(_TMP_DIR, 'twister_builder.lock')

logger = logging.getLogger(__name__)


class BuildStatus(str, Enum):
    NOT_DONE = 'NOT_DONE'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'
    FAILED = 'FAILED'


class BuildManager:
    """
    Class handles information about already built sources.

    It allows to skip building when it was already built for another test.
    """
    _lock: BaseFileLock = FileLock(BUILD_LOCK_FILE_PATH, timeout=1)

    def __init__(self, output_dir: str | Path, wait_build_timeout: int = 600) -> None:
        self._status_file: Path = Path(output_dir) / BUILD_STATUS_FILE_NAME
        self.wait_build_timeout: int = wait_build_timeout  # seconds
        self.initialize()

    def initialize(self):
        with self._lock:
            if self._status_file.exists():
                return
            logger.info('Create empty builder status file: %s', self._status_file)
            self._write_data({})

    def get_status(self, build_dir: str | Path) -> str:
        """
        Return status for build source.

        :param build_dir: path to build director
        :return: build status
        """
        with self._lock:
            data = self._read_data()
            return data.get(str(build_dir), BuildStatus.NOT_DONE)

    def _read_data(self) -> dict:
        with self._status_file.open(encoding='UTF-8') as file:
            data: dict = json.load(file)
        return data

    def update_status(self, build_dir: str | Path, status: str) -> bool:
        """
        Update status for build source.

        If new status is equal to old one than return False,
        otherwise return True

        :param build_dir: path to build director
        :param status: new status
        :return: True if status was updated otherwise return False
        """
        with self._lock:
            data = self._read_data()
            if data.get(build_dir) == status:
                return False
            data[str(build_dir)] = status
            self._write_data(data)
            return True

    def _write_data(self, data) -> None:
        with self._status_file.open('w', encoding='UTF-8') as file:
            json.dump(data, file, indent=2)

    def build(self, builder: BuilderAbstract, build_config: BuildConfig) -> None:
        """
        Build source code.

        :param builder: instance of a builder class
        :param build_config: build configuration
        """
        status: str = self.get_status(build_config.build_dir)
        if status == BuildStatus.DONE:
            logger.info('Already build in %s', build_config.build_dir)
            return
        if status == BuildStatus.NOT_DONE:
            if self.update_status(build_config.build_dir, BuildStatus.IN_PROGRESS):
                self._build(builder=builder, build_config=build_config)
                return
            else:
                status = self.get_status(build_config.build_dir)
        if status == BuildStatus.IN_PROGRESS:
            # another builder is building the same source
            self._wait_for_build_to_finish(build_config.build_dir)
            status = self.get_status(build_config.build_dir)
        if status == BuildStatus.FAILED:
            msg = f'Found in {self._status_file} the build status is set as {BuildStatus.FAILED} ' \
                  f'for: {build_config.build_dir}'
            logger.error(msg)
            raise TwisterBuildException(msg)

    def _build(self, builder: BuilderAbstract, build_config: BuildConfig) -> None:
        try:
            builder.build(build_config)
        except Exception:
            self.update_status(build_config.build_dir, BuildStatus.FAILED)
            raise
        else:
            self.update_status(build_config.build_dir, BuildStatus.DONE)

    def _wait_for_build_to_finish(self, build_dir: str | Path) -> None:
        logger.debug('Waiting for finishing building: %s', build_dir)
        timeout = time.time() + self.wait_build_timeout
        while self.get_status(build_dir) == BuildStatus.IN_PROGRESS:
            time.sleep(1)
            if time.time() > timeout:
                msg = f'Timed out waiting for another thread to finish building: {build_dir}'
                logger.error(msg)
                raise TwisterBuildException(msg)

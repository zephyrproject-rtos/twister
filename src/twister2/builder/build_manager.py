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
from twister2.exceptions import (
    TwisterBuildException,
    TwisterBuildSkipException,
    TwisterMemoryOverflowException,
)

_TMP_DIR: str = tempfile.gettempdir()
BUILD_STATUS_FILE_NAME: str = 'twister_builder.json'
BUILD_LOCK_FILE_PATH: str = os.path.join(_TMP_DIR, 'twister_builder.lock')

logger = logging.getLogger(__name__)


class BuildStatus(str, Enum):
    NOT_DONE = 'NOT_DONE'
    SKIPPED = 'SKIPPED'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'
    FAILED = 'FAILED'


class BuildManager:
    """
    Class handles information about already built sources.

    It allows to skip building when it was already built for another test.
    """
    _lock: BaseFileLock = FileLock(BUILD_LOCK_FILE_PATH, timeout=1)

    def __init__(self,
                 output_dir: str | Path,
                 build_config: BuildConfig,
                 builder: BuilderAbstract,
                 wait_build_timeout: int = 600) -> None:
        self._status_file: Path = Path(output_dir) / BUILD_STATUS_FILE_NAME
        self.wait_build_timeout: int = wait_build_timeout  # seconds
        self.build_config: BuildConfig = build_config
        self.builder: BuilderAbstract = builder
        self.initialize()

    def initialize(self):
        with self._lock:
            if self._status_file.exists():
                return
            logger.info('Create empty builder status file: %s', self._status_file)
            self._write_data({})

    def get_status(self) -> str:
        """
        Return status for build source.

        :return: build status
        """
        build_dir = str(self.build_config.build_dir)
        with self._lock:
            data = self._read_data()
            return data.get(build_dir, BuildStatus.NOT_DONE)

    def _read_data(self) -> dict:
        with self._status_file.open(encoding='UTF-8') as file:
            data: dict = json.load(file)
        return data

    def update_status(self, status: str) -> bool:
        """
        Update status for build source.

        If new status is equal to old one than return False,
        otherwise return True

        :param status: new status
        :return: True if status was updated otherwise return False
        """
        build_dir = str(self.build_config.build_dir)
        with self._lock:
            data = self._read_data()
            if data.get(build_dir) == status:
                return False
            data[build_dir] = status
            self._write_data(data)
            return True

    def _write_data(self, data) -> None:
        with self._status_file.open('w', encoding='UTF-8') as file:
            json.dump(data, file, indent=2)

    def build(self) -> None:
        """
        Build source code.
        """
        status: str = self.get_status()
        if status == BuildStatus.NOT_DONE:
            if self.update_status(BuildStatus.IN_PROGRESS):
                self._build(builder=self.builder)
                return
            else:
                status = self.get_status()
        if status == BuildStatus.IN_PROGRESS:
            # another builder is building the same source
            self._wait_for_build_to_finish()
            status = self.get_status()
        if status == BuildStatus.DONE:
            logger.info('Already build in %s', self.build_config.build_dir)
            return
        if status == BuildStatus.SKIPPED:
            msg = f'Found in {self._status_file} the build status is set as {BuildStatus.SKIPPED} ' \
                  f'for: {self.build_config.build_dir}'
            logger.info(msg)
            raise TwisterBuildSkipException(msg)
        if status == BuildStatus.FAILED:
            msg = f'Found in {self._status_file} the build status is set as {BuildStatus.FAILED} ' \
                  f'for: {self.build_config.build_dir}'
            logger.error(msg)
            raise TwisterBuildException(msg)

    def _build(self, builder: BuilderAbstract) -> None:
        try:
            builder.build(self.build_config)
        except TwisterMemoryOverflowException as overflow_exception:
            if self.build_config.overflow_as_errors:
                self.update_status(BuildStatus.FAILED)
                logger.error(overflow_exception)
            else:
                self.update_status(BuildStatus.SKIPPED)
                logger.info(overflow_exception)
            raise
        except Exception:
            self.update_status(BuildStatus.FAILED)
            raise
        else:
            self.update_status(BuildStatus.DONE)

    def _wait_for_build_to_finish(self) -> None:
        logger.debug('Waiting for finishing building: %s', self.build_config.build_dir)
        timeout = time.time() + self.wait_build_timeout
        while self.get_status() == BuildStatus.IN_PROGRESS:
            time.sleep(1)
            if time.time() > timeout:
                msg = f'Timed out waiting for another thread to finish building: {self.build_config.build_dir}'
                logger.error(msg)
                raise TwisterBuildException(msg)

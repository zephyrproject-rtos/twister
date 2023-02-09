from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from enum import Enum
from pathlib import Path

from filelock import BaseFileLock, FileLock

from twister2.builder.build_helper import BuildFilterProcessor
from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.exceptions import (
    TwisterBuildException,
    TwisterBuildFiltrationException,
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

    _basic_files_to_keep: list[str] = [
        os.path.join('zephyr', '.config'),
        'handler.log',
        'build.log',
        'device.log',
        'recording.csv',
        # below ones are needed to make --test-only work as well
        'Makefile',
        'CMakeCache.txt',
        'build.ninja',
        os.path.join('CMakeFiles', 'rules.ninja')
    ]

    def __init__(self,
                 build_config: BuildConfig,
                 builder: BuilderAbstract,
                 wait_build_timeout: int = 600) -> None:
        """
        :param build_config: build configuration
        :param builder: builder instance
        :param wait_build_timeout: timeout for building before it will be cancelled
        """
        self._status_file: Path = Path(build_config.output_dir) / BUILD_STATUS_FILE_NAME
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
            builder.run_cmake_stage()
            if self.build_config.cmake_filter:
                BuildFilterProcessor.apply_cmake_filtration(self.build_config)
            builder.run_build_generator()
        except TwisterMemoryOverflowException as overflow_exception:
            if self.build_config.overflow_as_errors:
                self.update_status(BuildStatus.FAILED)
                logger.error(overflow_exception)
            else:
                self.update_status(BuildStatus.SKIPPED)
                logger.info(overflow_exception)
            raise
        except TwisterBuildFiltrationException:
            self.update_status(BuildStatus.SKIPPED)
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

    def cleanup_artifacts(self, cleanup_version: str = '', additional_keep: list[str] | None = None) -> None:
        """
        Remove build output files to reduce memory consumption. Leave only this
        files which can be important to analyzing how the build was performed
        (mostly log files). For 'cleanup_version' set as 'all', keep additionally
        twister/testsuite_extra.conf file. By passing list of 'additional_keep'
        there is possibility to keep other files.
        """
        if additional_keep is None:
            additional_keep = []

        logger.debug('Cleaning up %s', self.build_config.build_dir)

        files_to_keep: list[str] = self._basic_files_to_keep.copy()

        if cleanup_version == 'all':
            files_to_keep += [os.path.join('twister', 'testsuite_extra.conf')]

        files_to_keep += additional_keep

        files_to_keep = [os.path.join(self.build_config.build_dir, file) for file in files_to_keep]

        for dirpath, dirnames, filenames in os.walk(self.build_config.build_dir, topdown=False):
            for name in filenames:
                path = os.path.join(dirpath, name)
                if path not in files_to_keep:
                    os.remove(path)
            # Remove empty directories and symbolic links to directories
            for dir in dirnames:
                path = os.path.join(dirpath, dir)
                if os.path.islink(path):
                    os.remove(path)
                elif not os.listdir(path):
                    os.rmdir(path)

    def prepare_device_testing_artifacts(self, binaries: list[str] | None = None) -> None:
        """
        Remove build output files to reduce memory consumption and keep only
        this files, which are necessary to reproduce test. By default
        'zephyr.hex', 'zephyr.bin' and 'zephyr.elf' files should be stored, but
        there is possibility to indicate other files by passing list them in
        'binaries' argument. Additionally local paths in 'CMakeCache.txt' and
        'zephyr/runners.yaml' files are removed to be able to make it possible
        to reuse them on different host/computer/server.
        """
        if binaries is None:
            binaries = []

        logger.debug('Cleaning up for Device Testing %d', self.build_config.build_dir)

        files_to_keep: list[str] = []
        if binaries:
            for binary in binaries:
                files_to_keep.append(os.path.join('zephyr', binary))
        else:
            files_to_keep = [
                os.path.join('zephyr', 'zephyr.hex'),
                os.path.join('zephyr', 'zephyr.bin'),
                os.path.join('zephyr', 'zephyr.elf'),
            ]

        files_to_sanitize: list[str] = [
            'CMakeCache.txt',
            os.path.join('zephyr', 'runners.yaml'),
        ]

        files_to_keep += files_to_sanitize

        self.cleanup_artifacts(additional_keep=files_to_keep)
        self._sanitize_output_paths(files_to_sanitize)

    def _sanitize_output_paths(self, files_to_sanitize: list[str]) -> None:
        """
        Sanitize files content to remove local Zephyr base paths.
        """
        for file in files_to_sanitize:
            file = os.path.join(self.build_config.build_dir, file)

            if os.path.isfile(file):
                with open(file, 'rt') as fin:
                    data = fin.read()
                    data = data.replace(str(self.build_config.zephyr_base) + os.path.sep, '')

                with open(file, 'wt') as fin:
                    fin.write(data)

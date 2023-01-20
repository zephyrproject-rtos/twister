from __future__ import annotations

import logging
import shutil
import subprocess

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.exceptions import TwisterBuildException
from twister2.helper import log_command

logger = logging.getLogger(__name__)


class CmakeBuilder(BuilderAbstract):
    """Build source code using `cmake`"""

    def build(self, cmake_helper: bool = False) -> None:
        """
        Build Zephyr application with `cmake`.

        :param cmake_helper: if True only CMake package helper should be run, without full building
        """
        logger.info('Building Zephyr application')
        self.run_cmake(cmake_helper)
        if cmake_helper:
            return
        self.run_build_generator()

    def run_cmake(self, cmake_helper: bool = False) -> None:
        cmake = self._get_cmake()

        command = [
            cmake,
            f'-S{self.build_config.source_dir}',
            f'-B{self.build_config.build_dir}',
            f'-DBOARD={self.build_config.platform_name}'
        ]

        if cmake_args := self._prepare_cmake_args(self.build_config):
            command.extend(cmake_args)

        if cmake_helper:
            command.extend(
                [
                    '-DMODULES=dts,kconfig',
                    f'-P{self.build_config.zephyr_base}/cmake/package_helper.cmake',
                ]
            )

        log_command(logger, 'Cmake command', command, level=logging.INFO)
        self._run_command_in_subprocess(command, action='Cmake')

    def run_build_generator(self) -> None:
        cmake = self._get_cmake()
        command: list[str] = [cmake, '--build', str(self.build_config.build_dir)]
        log_command(logger, 'Build command', command, level=logging.INFO)
        self._run_command_in_subprocess(command, action='building')

    def _run_command_in_subprocess(self, command: list[str], action: str) -> None:
        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            logger.exception(
                'An exception has been raised for %s: %s for %s',
                action, self.build_config.source_dir, self.build_config.platform_name
            )
            raise TwisterBuildException('CMake error') from e
        else:
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info(
                    'Finished running CMake on %s for %s',
                    self.build_config.source_dir, self.build_config.platform_name
                )
            else:
                self._log_output(process.stdout, logging.INFO)
                msg = (
                    f'Failed running CMake {self.build_config.source_dir} '
                    f'for platform: {self.build_config.platform_name}'
                )
                logger.error(msg)
                raise TwisterBuildException(msg)

    @staticmethod
    def _get_cmake() -> str:
        if (cmake := shutil.which('cmake')) is None:
            raise TwisterBuildException('cmake not found')
        return cmake

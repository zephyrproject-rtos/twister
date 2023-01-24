from __future__ import annotations

import logging
import shutil

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.exceptions import TwisterBuildException
from twister2.helper import log_command

logger = logging.getLogger(__name__)


class CMakeBuilder(BuilderAbstract):
    """Build source code using `cmake`"""

    def build(self) -> None:
        """Build source code using `cmake`"""
        logger.info('Building Zephyr application')
        self.run_cmake_stage()
        self.run_build_generator()

    def run_cmake_stage(self, cmake_helper: bool = False) -> None:
        """
        Run CMake for source code.

        :param cmake_helper: if True only CMake package helper should be run, without full building
        """
        cmake = self._get_cmake()

        command = [
            cmake,
            f'-S{self.build_config.source_dir}',
            f'-B{self.build_config.build_dir}',
            '-GNinja',
            f'-DBOARD={self.build_config.platform_name}',
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

        log_command(logger, 'CMake command', command, level=logging.INFO)
        self._run_command_in_subprocess(command, action='CMake')

    def run_build_generator(self) -> None:
        cmake = self._get_cmake()
        command: list[str] = [cmake, '--build', str(self.build_config.build_dir)]
        log_command(logger, 'Build command', command, level=logging.INFO)
        self._run_command_in_subprocess(command, action='building')

    @staticmethod
    def _get_cmake() -> str:
        if (cmake := shutil.which('cmake')) is None:
            raise TwisterBuildException('cmake not found')
        return cmake

from __future__ import annotations

import logging
import shutil

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.exceptions import TwisterBuildException
from twister2.helper import log_command

logger = logging.getLogger(__name__)


class WestBuilder(BuilderAbstract):
    """Build source code using `west`"""

    def build(self) -> None:
        """
        Build Zephyr application with `west`.
        """
        logger.info('Building Zephyr application')

        command = self._generate_west_command(cmake_only=False)

        log_command(logger, 'West building command', command, level=logging.INFO)
        self._run_command_in_subprocess(command, action='west building')

    def run_cmake_stage(self, cmake_helper: bool = False) -> None:
        """
        Run west with "--cmake-only" option enabled
        """
        command = self._generate_west_command(cmake_only=True)

        log_command(logger, 'West --cmake-only command', command, level=logging.INFO)
        self._run_command_in_subprocess(command, action='west --cmake-only')

    def run_build_generator(self) -> None:
        """
        Run west without pristine option - if cmake was already run before, then only build generator (e.g. Ninja) will
        be executed. Please run this method only if you are sure that build directory was already generated by Cmake.
        """
        west = self._get_west()

        command = [west, 'build', '--build-dir', str(self.build_config.build_dir)]

        log_command(logger, 'West building command', command, level=logging.INFO)
        self._run_command_in_subprocess(command, action='west building')

    def _generate_west_command(self, cmake_only: bool = False) -> list[str]:
        west = self._get_west()

        command = [west, 'build']

        if cmake_only:
            command.extend(['--cmake-only'])

        command += [
            '--pristine', 'always',
            '--board', self.build_config.platform_name,
            '--build-dir', str(self.build_config.build_dir),
            str(self.build_config.source_dir),
        ]

        if self.build_config.cmake_extra_args:
            command.extend(['--'] + self.build_config.cmake_extra_args)

        return command

    @staticmethod
    def _get_west() -> str:
        if (west := shutil.which('west')) is None:
            raise TwisterBuildException('west not found')
        return west

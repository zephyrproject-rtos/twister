from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.exceptions import TwisterBuildException

logger = logging.getLogger(__name__)


class WestBuilder(BuilderAbstract):

    def build(self, platform: str, scenario: str, build_dir: str | Path | None = None, **kwargs) -> None:
        """
        Build Zephyr application with `west`.

        :param platform: board to build for with optional board revision
        :param build_dir: build directory to create or use
        :param scenario: test scenario name
        :keyword cmake_args: list of extra cmake arguments
        """
        west = shutil.which('west')
        command = [
            west,
            'build',
            str(self.source_dir),
            '--pristine', 'always',
            '--board', platform,
            '--test-item', scenario
        ]
        if build_dir:
            command.extend(['--build-dir', str(build_dir)])
        if cmake_args := kwargs.get('cmake_args'):
            args = self._prepare_cmake_args(cmake_args)
            command.extend(['--', args])

        logger.info('Building Zephyr application')
        logger.info('Build command: %s', ' '.join(command))
        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            logger.error('Failed building %s for %s', self.source_dir, platform)
            raise TwisterBuildException('Building error') from e
        else:
            if process.returncode == 0:
                logger.info('Finished building %s for %s', self.source_dir, platform)
            else:
                logger.error(process.stderr.decode())
                raise TwisterBuildException(f'Failed building {self.source_dir} for {platform}')

    @staticmethod
    def _prepare_cmake_args(cmake_args: list[str]) -> str:
        args_joined = ' '.join([f'-D{arg}' for arg in cmake_args])
        if ' ' in args_joined:
            return f'"{args_joined}"'
        return f'{args_joined}'

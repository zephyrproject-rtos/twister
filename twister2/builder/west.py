from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.exceptions import TwisterBuildException

logger = logging.getLogger(__name__)


class WestBuilder(BuilderAbstract):

    def build(self, platform: str, build_dir: str | Path | None = None, **kwargs) -> None:
        """
        Build Zephyr application.

        :param platform: board to build for with optional board revision
        :param build_dir: build directory to create or use
        :keyword cmake_args: list of extra cmake arguments
        """
        west = shutil.which('west')
        command = [
            west,
            'build',
            '--pristine', 'always',
            '--board', platform,
            str(self.source_dir),
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
                cwd=self.zephyr_base.resolve(),
                env=self.env,
            )
        except subprocess.CalledProcessError as e:
            logger.error('Failed building %s for %s', self.source_dir, platform)
            raise TwisterBuildException('Building error') from e
        else:
            if process.returncode == 0:
                logger.info('Finished building %s for %s', self.source_dir, platform)
            else:
                logger.error(process.stderr.decode())
                raise TwisterBuildException('Failed building %s for %s', self.source_dir, platform)

    @staticmethod
    def _prepare_cmake_args(cmake_args: list[str]) -> str:
        args_joined = ' '.join([f'-D{arg}' for arg in cmake_args])
        return f'"{args_joined}"'

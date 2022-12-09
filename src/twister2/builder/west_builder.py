from __future__ import annotations

import logging
import shutil
import subprocess

from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.exceptions import TwisterBuildException
from twister2.helper import log_command

logger = logging.getLogger(__name__)


class WestBuilder(BuilderAbstract):

    def build(self, build_config: BuildConfig) -> None:
        """
        Build Zephyr application with `west`.
        """
        if (west := shutil.which('west')) is None:
            raise TwisterBuildException('west not found')

        command = [
            west,
            'build',
            str(build_config.source_dir),
            '--pristine', 'always',
            '--board', build_config.platform,
            '--test-item', build_config.scenario
        ]
        if build_config.build_dir:
            command.extend(['--build-dir', str(build_config.build_dir)])
        if cmake_args := build_config.extra_args:
            args = self._prepare_cmake_args(cmake_args)
            command.extend(['--', args])

        logger.info('Building Zephyr application')
        log_command(logger, 'Build command', command, level=logging.INFO)
        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            logger.exception(
                'An exception has been raised for build subprocess: %s for %s',
                build_config.source_dir, build_config.platform
            )
            raise TwisterBuildException('Building error') from e
        else:
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info('Finished building %s for %s', build_config.source_dir, build_config.platform)
            else:
                self._log_output(process.stdout, logging.INFO)
                msg = f'Failed building {build_config.source_dir} for platform: {build_config.platform}'
                logger.error(msg)
                raise TwisterBuildException(msg)

    @staticmethod
    def _log_output(output: bytes, level: int) -> None:
        for line in output.decode().split('\n'):
            logger.log(level, line)

    @staticmethod
    def _prepare_cmake_args(cmake_args: list[str]) -> str:
        args_joined = ' '.join([f'-D{arg}' for arg in cmake_args])
        if ' ' in args_joined:
            return f'"{args_joined}"'
        return f'{args_joined}'

from __future__ import annotations

import logging
import re
import shutil
import subprocess

from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.exceptions import TwisterBuildException, TwisterMemoryOverflowException
from twister2.helper import log_command

logger = logging.getLogger(__name__)


class WestBuilder(BuilderAbstract):
    """Build source code using `west`"""

    def build(self, cmake_helper: bool = False) -> None:
        """
        Build Zephyr application with `west`.
        """
        if (west := shutil.which('west')) is None:
            raise TwisterBuildException('west not found')

        command = [
            west,
            'build',
            str(self.build_config.source_dir),
            '--pristine', 'always',
            '--board', self.build_config.platform_name,
        ]
        if self.build_config.build_dir:
            command.extend(['--build-dir', str(self.build_config.build_dir)])
        if cmake_args := self._prepare_cmake_args(self.build_config):
            command.extend(['--'] + cmake_args)

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
                self.build_config.source_dir, self.build_config.platform_name
            )
            raise TwisterBuildException('Building error') from e
        else:
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info(
                    'Finished building %s for %s',
                    self.build_config.source_dir, self.build_config.platform_name
                )
            else:
                self._handle_build_failure(self.build_config, process.stdout)

    def _handle_build_failure(self, build_config: BuildConfig, stdout_output: bytes):
        self._log_output(stdout_output, logging.INFO)
        self._check_memory_overflow(build_config, stdout_output)
        msg = f'Failed building {build_config.source_dir} for platform: {build_config.platform_name}'
        logger.error(msg)
        raise TwisterBuildException(msg)

    @staticmethod
    def _check_memory_overflow(build_config: BuildConfig, output: bytes) -> None:
        build_output = output.decode()
        memory_overflow_pattern = 'region `(FLASH|ROM|RAM|ICCM|DCCM|SRAM|dram0_1_seg)\' overflowed by'
        imgtool_overflow_pattern = r'Error: Image size \(.*\) \+ trailer \(.*\) exceeds requested size'
        memory_overflow_found = re.findall(memory_overflow_pattern, build_output)
        if memory_overflow_found:
            msg = f'Memory overflow during building {build_config.source_dir} for platform: ' \
                  f'{build_config.platform_name}'
            raise TwisterMemoryOverflowException(msg)
        imgtool_overflow_found = re.findall(imgtool_overflow_pattern, build_output)
        if imgtool_overflow_found:
            msg = f'Imgtool memory overflow during building {build_config.source_dir} for platform: ' \
                  f'{build_config.platform_name}'
            raise TwisterMemoryOverflowException(msg)

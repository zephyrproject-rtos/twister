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
        ]
        if build_config.build_dir:
            command.extend(['--build-dir', str(build_config.build_dir)])
        if cmake_args := self._prepare_cmake_args(build_config):
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
                build_config.source_dir, build_config.platform
            )
            raise TwisterBuildException('Building error') from e
        else:
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info('Finished building %s for %s', build_config.source_dir, build_config.platform)
            else:
                self._handle_build_failure(build_config, process.stdout)

    def _prepare_cmake_args(self, build_config: BuildConfig) -> list[str]:
        """
        "extra_configs" and "extra_args" which came from .yaml file are unpacked
        and parsed here to avoid limitation of west "--test-item" option which
        works properly only with testcase.yaml and sample.yaml files.
        "--test-item" option doesn't work with unorthodox .yaml files like
        testspec.yaml file.
        """
        cmake_args = []

        cmake_args += (self._prepare_extra_configs(build_config.extra_configs))
        cmake_args += (self._prepare_args(build_config.extra_args_spec))
        cmake_args += (self._prepare_args(build_config.extra_args_cli))

        return cmake_args

    @staticmethod
    def _prepare_args(args: list[str]) -> list[str]:
        return ['-D{}'.format(arg.replace('"', '')) for arg in args]

    @staticmethod
    def _prepare_extra_configs(args: list[str]) -> list[str]:
        return ['-D{}'.format(arg) for arg in args]

    def _handle_build_failure(self, build_config: BuildConfig, stdout_output: bytes):
        self._log_output(stdout_output, logging.INFO)
        self._check_memory_overflow(build_config, stdout_output)
        msg = f'Failed building {build_config.source_dir} for platform: {build_config.platform}'
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
                  f'{build_config.platform}'
            raise TwisterMemoryOverflowException(msg)
        imgtool_overflow_found = re.findall(imgtool_overflow_pattern, build_output)
        if imgtool_overflow_found:
            msg = f'Imgtool memory overflow during building {build_config.source_dir} for platform: ' \
                  f'{build_config.platform}'
            raise TwisterMemoryOverflowException(msg)

    @staticmethod
    def _log_output(output: bytes, level: int) -> None:
        for line in output.decode().split('\n'):
            logger.log(level, line)

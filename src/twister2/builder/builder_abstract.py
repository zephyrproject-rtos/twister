from __future__ import annotations

import abc
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from twister2.exceptions import TwisterBuildException, TwisterMemoryOverflowException
from twister2.log_files.log_file import BuildLogFile

logger = logging.getLogger(__name__)


@dataclass
class BuildConfig:
    """Class store all information required by builder to build a source code."""
    zephyr_base: str | Path
    source_dir: str | Path
    output_dir: str | Path
    build_dir: str | Path
    platform_arch: str
    platform_name: str
    scenario: str
    cmake_filter: str
    cmake_extra_args: list[str] = field(default_factory=list)
    overflow_as_errors: bool = field(default_factory=bool)


class BuilderAbstract(abc.ABC):
    """Base class for builders."""

    def __init__(self, build_config: BuildConfig) -> None:
        self.build_config = build_config
        self.build_log_file = BuildLogFile.create(build_dir=self.build_config.build_dir)

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    @abc.abstractmethod
    def build(self) -> None:
        """
        Build Zephyr application.
        """

    def run_cmake_stage(self, cmake_helper: bool = False) -> None:
        """
        Run CMake only without running build generator.
        """

    def run_build_generator(self) -> None:
        """
        Run build generator like Ninja or Makefile to build application
        """

    def _handle_build_failure(self, build_config: BuildConfig, stdout_output: bytes, action: str):
        self._log_output(stdout_output, logging.INFO)
        self._check_memory_overflow(build_config, stdout_output)
        msg = f'Failed {action} {build_config.source_dir} for platform: {build_config.platform_name}'
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

    def _run_command_in_subprocess(self, command: list[str], action: str) -> None:
        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            self.build_log_file.handle(e.cmd)
            logger.exception(
                'An exception has been raised for %s: %s for %s',
                action, self.build_config.source_dir, self.build_config.platform_name
            )
            raise TwisterBuildException(f'{action} error') from e
        else:
            self.build_log_file.handle(process.stdout)
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info(
                    'Finished running %s on %s for %s',
                    action, self.build_config.source_dir, self.build_config.platform_name
                )
            else:
                self._handle_build_failure(self.build_config, process.stdout, action)

    @staticmethod
    def _log_output(output: bytes, level: int) -> None:
        for line in output.decode().split('\n'):
            logger.log(level, line)

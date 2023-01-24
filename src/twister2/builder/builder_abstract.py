from __future__ import annotations

import abc
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from twister2.exceptions import TwisterBuildException, TwisterMemoryOverflowException

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
    extra_configs: list[str] = field(default_factory=list)
    extra_args_spec: list[str] = field(default_factory=list)
    extra_args_cli: list[str] = field(default_factory=list)
    overflow_as_errors: bool = field(default_factory=bool)


class BuilderAbstract(abc.ABC):
    """Base class for builders."""

    def __init__(self, build_config: BuildConfig) -> None:
        self.build_config = build_config

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

    def _prepare_cmake_args(self, build_config: BuildConfig) -> list[str]:
        """
        "extra_configs" and "extra_args" which came from .yaml file are unpacked
        and parsed here to avoid limitation of west "--test-item" option which
        works properly only with testcase.yaml and sample.yaml files.
        "--test-item" option doesn't work with unorthodox .yaml files like
        testspec.yaml file.
        """
        cmake_args = []

        ldflags = '-Wl,--fatal-warnings'
        cflags = '-Werror'
        aflags = '-Werror -Wa,--fatal-warnings'
        gen_defines_args = '--edtlib-Werror'

        cmake_args += [
            f'-DEXTRA_CFLAGS={cflags}',
            f'-DEXTRA_AFLAGS={aflags}',
            f'-DEXTRA_LDFLAGS={ldflags}',
            f'-DEXTRA_GEN_DEFINES_ARGS={gen_defines_args}',
        ]

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

    @staticmethod
    def _log_output(output: bytes, level: int) -> None:
        for line in output.decode().split('\n'):
            logger.log(level, line)

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
            logger.exception(
                'An exception has been raised for %s: %s for %s',
                action, self.build_config.source_dir, self.build_config.platform_name
            )
            raise TwisterBuildException(f'{action} error') from e
        else:
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info(
                    'Finished running %s on %s for %s',
                    action, self.build_config.source_dir, self.build_config.platform_name
                )
            else:
                self._handle_build_failure(self.build_config, process.stdout, action)

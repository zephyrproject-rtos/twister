from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from pathlib import Path

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
    kconfig_dts_filter: str
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
    def build(self, cmake_helper: bool = False) -> None:
        """
        Build Zephyr application.

        :param cmake_helper: if True only CMake package helper should be run, without full building
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

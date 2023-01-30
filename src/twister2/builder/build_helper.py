from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.cmake_filter.cmake_filter import CMakeFilter
from twister2.exceptions import TwisterBuildFiltrationException

logger = logging.getLogger(__name__)


class BuildFilterProcessor:
    """Run additional setup before actual build is triggered."""

    def __init__(self, builder: BuilderAbstract) -> None:
        self.builder = builder

    def process(self) -> None:
        """Run build with cmake_helper flag enabled."""
        self.builder.run_cmake_stage(True)
        self.apply_cmake_filtration(self.builder.build_config)

    @staticmethod
    def apply_cmake_filtration(build_config: BuildConfig) -> None:
        cmake_filter = CMakeFilter(
            build_config.zephyr_base,
            build_config.build_dir,
            build_config.platform_arch,
            build_config.platform_name,
            build_config.cmake_filter
        )
        result: bool = cmake_filter.filter()
        if result is False:
            msg = 'runtime filter - build configuration do not fullfil Kconfig, DTS or other CMake requirements'
            logger.info(msg)
            raise TwisterBuildFiltrationException(msg)


@dataclass
class CMakeExtraArgsConfig:
    """Class store all information required to generate extra CMake extra args."""
    run_id: str
    build_dir: Path
    device_type: str
    fifo_file: Path
    platform_arch: str
    platform_name: str
    extra_args_spec: list[str] = field(default_factory=list)
    extra_configs: list[str] = field(default_factory=list)
    extra_args_cli: list[str] = field(default_factory=list)


class CMakeExtraArgsGenerator:
    """
    Generate CMake extra arguments, which can be used in CMake command
    during building process.
    """
    def __init__(self, config: CMakeExtraArgsConfig) -> None:
        self.config = config

    def generate(self) -> list[str]:
        """
        Generate ready to use CMake extra arguments according to passed
        CMakeExtraArgsConfig configuration.
        """

        cmake_args = []
        cmake_args.append(f'-DTC_RUNID={self.config.run_id}')
        cmake_args += self._prepare_warning_as_error_args()

        extra_args = self.config.extra_args_spec
        extra_args += self._prepare_extra_configs()

        cmake_args += self._prepare_extra_args_spec(extra_args)

        if self.config.device_type == 'qemu':
            cmake_args.append(f'-DQEMU_PIPE={str(self.config.fifo_file)}')

        cmake_args += self._prepare_extra_args_cli(self.config.extra_args_cli)

        return cmake_args

    @staticmethod
    def _prepare_warning_as_error_args() -> list[str]:
        ldflags = '-Wl,--fatal-warnings'
        cflags = '-Werror'
        aflags = '-Werror -Wa,--fatal-warnings'
        gen_defines_args = '--edtlib-Werror'

        args = [
            f'-DEXTRA_CFLAGS={cflags}',
            f'-DEXTRA_AFLAGS={aflags}',
            f'-DEXTRA_LDFLAGS={ldflags}',
            f'-DEXTRA_GEN_DEFINES_ARGS={gen_defines_args}',
        ]
        return args

    def _prepare_extra_configs(self) -> list[str]:
        extra_configs_overlay: str = ''

        if self.config.extra_configs:
            parsed_extra_configs = self._parse_extra_configs()
            extra_configs_overlay = '\n'.join(parsed_extra_configs)

        additional_extra_args = []
        if extra_configs_overlay:
            extra_configs_file_path = self._export_overlay_config(self.config.build_dir, extra_configs_overlay)
            additional_extra_args.append(f'OVERLAY_CONFIG="{str(extra_configs_file_path)}"')

        return additional_extra_args

    def _parse_extra_configs(self) -> list[str]:
        """
        Some configs might be conditional on arch or platform, see if we
        have a namespace defined and apply only if the namespace matches.
        we currently support both arch and platform conditions, like for
        example:
        arch:arm:CONFIG_BOOT_BANNER=n
        platform:natvie_posix:CONFIG_BOOT_BANNER=n
        """
        parsed_extra_configs = []
        for config in self.config.extra_configs:
            cond_config = config.split(':')
            if cond_config[0] == 'arch' and len(cond_config) == 3:
                if self.config.platform_arch == cond_config[1]:
                    parsed_extra_configs.append(cond_config[2])
            elif cond_config[0] == 'platform' and len(cond_config) == 3:
                if self.config.platform_name == cond_config[1]:
                    parsed_extra_configs.append(cond_config[2])
            else:
                parsed_extra_configs.append(config)
        return parsed_extra_configs

    @staticmethod
    def _export_overlay_config(build_dir: str | Path, extra_configs_overlay: str) -> Path:
        extra_configs_dir = Path(build_dir) / 'twister'
        extra_configs_file_path = extra_configs_dir / 'testsuite_extra.conf'
        os.makedirs(extra_configs_dir, exist_ok=True)
        with open(extra_configs_file_path, 'w') as file:
            file.write(extra_configs_overlay)
        return extra_configs_file_path

    def _prepare_extra_args_spec(self, args: list[str]) -> list[str]:
        """
        To be compatible with Twister v1 this method merge all OVERLAY_CONFIG
        arguments into one argument and remove '"' from each option.
        """
        args = self._merge_overlay_config(args)
        return ['-D{}'.format(arg.replace('"', '')) for arg in args]

    @staticmethod
    def _merge_overlay_config(args: list[str]) -> list[str]:
        args_modified = []
        overlay_config_paths = []
        re_overlay_config = re.compile(r'^\s*OVERLAY_CONFIG=(.*)')
        for arg in args:
            match = re_overlay_config.search(arg)
            if match:
                overlay_config_paths.append(match.group(1).strip('\'"'))
            else:
                args_modified.append(arg)

        if overlay_config_paths:
            overlay_config_value = ' '.join(overlay_config_paths)
            args_modified.append(f'OVERLAY_CONFIG=\"{overlay_config_value}\"')

        return args_modified

    @staticmethod
    def _prepare_extra_args_cli(args: list[str]) -> list[str]:
        """
        To be compatible with Twister v1 this method replace '"' into '\"' in
        CMake arguments passed via CLI by user.
        """
        return ['-D{}'.format(arg.replace('"', '\"')) for arg in args]

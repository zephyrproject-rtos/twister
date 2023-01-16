from __future__ import annotations

import logging
import pytest
import shutil
import subprocess

from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.builder.kconfig_dts_filter import KconfigDtsFilter
from twister2.exceptions import TwisterBuildException
from twister2.helper import log_command

logger = logging.getLogger(__name__)


class WestBuilder(BuilderAbstract):

    def build(self, build_config: BuildConfig) -> None:
        """
        Build Zephyr application with `west`.
        """

        cmake_extra_args = self._prepare_cmake_args(build_config)

        if build_config.kconfig_dts_filter:
            self._run_cmake_helper(build_config, cmake_extra_args)
            self._apply_kconfig_and_dts_filtration(build_config)

        if (west := shutil.which('west')) is None:
            raise TwisterBuildException('west not found')

        command = [
            west,
            'build',
            str(build_config.source_dir),
            '--pristine', 'always',
            '--board', build_config.platform_name,
        ]
        if build_config.build_dir:
            command.extend(['--build-dir', str(build_config.build_dir)])
        if cmake_extra_args:
            command.extend(['--'] + cmake_extra_args)

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
                build_config.source_dir, build_config.platform_name
            )
            raise TwisterBuildException('Building error') from e
        else:
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info('Finished building %s for %s', build_config.source_dir, build_config.platform_name)
            else:
                self._log_output(process.stdout, logging.INFO)
                msg = f'Failed building {build_config.source_dir} for platform: {build_config.platform_name}'
                logger.error(msg)
                raise TwisterBuildException(msg)

    def _prepare_cmake_args(self, build_config: BuildConfig) -> list[str]:
        """
        "extra_configs" and "extra_args" which came from .yaml file are unpacked
        and parsed here to avoid limitation of west "--test-item" option which
        works properly only with testcase.yaml and sample.yaml files.
        "--test-item" option doesn't work with unorthodox .yaml files like
        testspec.yaml file.
        """
        cmake_args = []

        ldflags = "-Wl,--fatal-warnings"
        cflags = "-Werror"
        aflags = "-Werror -Wa,--fatal-warnings"
        gen_defines_args = "--edtlib-Werror"

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

    def _run_cmake_helper(self, build_config: BuildConfig, cmake_extra_args: list[str]):
        if (cmake := shutil.which('cmake')) is None:
            raise TwisterBuildException('cmake not found')

        command = [
            cmake,
            f'-S{build_config.source_dir}',
            f'-B{build_config.build_dir}',
            f'-DBOARD={build_config.platform_name}',
            *cmake_extra_args,
            '-DMODULES=dts,kconfig',
            f'-P{build_config.zephyr_base}/cmake/package_helper.cmake',
        ]

        # command += cmake_extra_args

        logger.info('Run CMake package helper')
        log_command(logger, 'CMake package helper', command, level=logging.INFO)
        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            logger.exception(
                'An exception has been raised for CMake: %s for %s',
                build_config.source_dir, build_config.platform_name
            )
            raise TwisterBuildException('CMake error') from e
        else:
            if process.returncode == 0:
                self._log_output(process.stdout, logging.DEBUG)
                logger.info('Finished running CMake on %s for %s', build_config.source_dir, build_config.platform_name)
            else:
                self._log_output(process.stdout, logging.INFO)
                msg = f'Failed running CMake {build_config.source_dir} for platform: {build_config.platform_name}'
                logger.error(msg)
                raise TwisterBuildException(msg)

    def _apply_kconfig_and_dts_filtration(self, build_config: BuildConfig) -> None:
        kconfig_dts_filter = KconfigDtsFilter(build_config.zephyr_base, build_config.build_dir,
                                              build_config.platform_arch, build_config.platform_name,
                                              build_config.kconfig_dts_filter)
        result = kconfig_dts_filter.filter()
        if not result:
            pytest.skip("Kconfig or dts filtration")

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

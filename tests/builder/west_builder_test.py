from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from twister2.builder.builder_abstract import BuildConfig
from twister2.builder.west_builder import WestBuilder
from twister2.exceptions import TwisterBuildException

DEFAULT_CMAKE_ARGS: list[str] = [
    '-DEXTRA_CFLAGS=-Werror',
    '-DEXTRA_AFLAGS=-Werror -Wa,--fatal-warnings',
    '-DEXTRA_LDFLAGS=-Wl,--fatal-warnings',
    '-DEXTRA_GEN_DEFINES_ARGS=--edtlib-Werror'
]


def test_prepare_cmake_args_with_no_extra_args(west_builder: WestBuilder, build_config: BuildConfig):
    build_config.extra_configs = []
    build_config.extra_args_spec = []
    build_config.extra_args_cli = []
    assert west_builder._prepare_cmake_args(build_config) == DEFAULT_CMAKE_ARGS


def test_prepare_cmake_args_with_one_extra_arg(west_builder: WestBuilder, build_config: BuildConfig):
    assert west_builder._prepare_cmake_args(build_config) == DEFAULT_CMAKE_ARGS + ['-DCONF_FILE=prj_single.conf']


def test_prepare_cmake_args_with_several_extra_args(west_builder: WestBuilder, build_config: BuildConfig):
    build_config.extra_configs = ['CONFIG_BOOT_BANNER=n']
    build_config.extra_args_spec = ['CONF_FILE=prj_single.conf']
    build_config.extra_args_cli = ['CONFIG_BOOT_DELAY=600']
    prepared_cmake_args = ['-DCONFIG_BOOT_BANNER=n', '-DCONF_FILE=prj_single.conf', '-DCONFIG_BOOT_DELAY=600']
    assert west_builder._prepare_cmake_args(build_config) == DEFAULT_CMAKE_ARGS + prepared_cmake_args


@mock.patch('shutil.which', return_value='west')
@mock.patch('subprocess.run')
def test_if_west_builder_builds_code_from_source_without_errors(
        patched_run, patched_which, west_builder: WestBuilder, build_config: BuildConfig
):
    mocked_process = mock.MagicMock()
    mocked_process.returncode = 0
    patched_run.return_value = mocked_process
    west_builder.build()
    patched_run.assert_called_with(
        ['west', 'build', '--pristine', 'always',
         '--board', build_config.platform_name,
         '--build-dir', build_config.build_dir, build_config.source_dir,
         '--'] + DEFAULT_CMAKE_ARGS + ['-DCONF_FILE=prj_single.conf'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )


@mock.patch('shutil.which', return_value='west')
@mock.patch('subprocess.run')
def test_if_west_builder_raises_exception_when_subprocess_returned_not_zero_returncode(
        patched_run, patched_which, west_builder: WestBuilder
):
    mocked_process = mock.MagicMock()
    mocked_process.returncode = 1
    mocked_process.stdout = 'fake build output'.encode()
    patched_run.return_value = mocked_process
    with pytest.raises(TwisterBuildException, match='Failed west building source for platform: native_posix'):
        west_builder.build()


@mock.patch('shutil.which', return_value='west')
@mock.patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'test'))
def test_if_west_builder_raises_exception_when_subprocess_raised_exception(
        patched_run, patched_which, west_builder: WestBuilder
):
    with pytest.raises(TwisterBuildException, match='west building error'):
        west_builder.build()


@mock.patch('shutil.which', return_value=None)
def test_it_west_builder_raises_exception_when_west_was_not_found(
        patched_which, west_builder: WestBuilder
):
    with pytest.raises(TwisterBuildException, match='west not found'):
        west_builder.build()

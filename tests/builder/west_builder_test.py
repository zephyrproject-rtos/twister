from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from twister2.builder.builder_abstract import BuildConfig
from twister2.builder.west_builder import WestBuilder
from twister2.exceptions import TwisterBuildException


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
         '--'] + build_config.cmake_extra_args,
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

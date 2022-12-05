import subprocess
from unittest import mock

import pytest

from twister2.builder.west_builder import WestBuilder
from twister2.exceptions import TwisterBuildException


@pytest.fixture(name='west_builder')
def fixture_west_builder():
    """Return west builder"""
    return WestBuilder(zephyr_base='zephyr', source_dir='source')


def test_prepare_cmake_args_with_no_args(west_builder: WestBuilder):
    cmake_args = []
    assert west_builder._prepare_cmake_args(cmake_args=cmake_args) == ''


def test_prepare_cmake_args_with_one_arg(west_builder: WestBuilder):
    cmake_args = ['FORKS=FIFOS']
    assert west_builder._prepare_cmake_args(cmake_args=cmake_args) == '-DFORKS=FIFOS'


def test_prepare_cmake_args_with_two_args(west_builder: WestBuilder):
    cmake_args = ['FORKS=FIFOS', 'CONF_FILE=prj_single.conf']
    assert west_builder._prepare_cmake_args(cmake_args=cmake_args) == '"-DFORKS=FIFOS -DCONF_FILE=prj_single.conf"'


@mock.patch('shutil.which', return_value='west')
@mock.patch('subprocess.run')
def test_if_west_builder_builds_code_from_source_without_errors(patched_run, patched_which, west_builder: WestBuilder):
    mocked_process = mock.MagicMock()
    mocked_process.returncode = 0
    patched_run.return_value = mocked_process
    west_builder.build(platform='native_posix', scenario='bt', build_dir='src', cmake_args=['CONFIG_NEWLIB_LIBC=y'])
    patched_run.assert_called_with(
        ['west', 'build', 'source', '--pristine', 'always', '--board', 'native_posix',
         '--test-item', 'bt', '--build-dir', 'src', '--', '-DCONFIG_NEWLIB_LIBC=y'],
        stdout=-1, stderr=-1
    )


@mock.patch('shutil.which', return_value='west')
@mock.patch('subprocess.run')
def test_if_west_builder_raises_exception_when_subprocess_returned_not_zero_returncode(
        patched_run, patched_which, west_builder: WestBuilder
):
    mocked_process = mock.MagicMock()
    mocked_process.returncode = 1
    patched_run.return_value = mocked_process
    with pytest.raises(TwisterBuildException, match='Failed building source for platform: native_posix'):
        west_builder.build(platform='native_posix', scenario='bt', build_dir='src')


@mock.patch('shutil.which', return_value='west')
@mock.patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'test'))
def test_if_west_builder_raises_exception_when_subprocess_raised_exception(
        patched_run, patched_which, west_builder: WestBuilder
):
    with pytest.raises(TwisterBuildException, match='Building error'):
        west_builder.build(platform='native_posix', scenario='bt', build_dir='src')


@mock.patch('shutil.which', return_value=None)
def test_it_west_builder_raises_exception_when_west_was_not_found(patched_which, west_builder: WestBuilder):
    with pytest.raises(TwisterBuildException, match='west not found'):
        west_builder.build(platform='native_posix', scenario='bt', build_dir='src')

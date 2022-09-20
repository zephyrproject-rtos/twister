import pytest

from twister2.builder.west import WestBuilder


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

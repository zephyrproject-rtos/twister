import pytest

from twister2.builder.builder_abstract import BuildConfig
from twister2.builder.cmake_builder import CMakeBuilder
from twister2.builder.west_builder import WestBuilder


@pytest.fixture
def build_config(tmpdir_factory) -> BuildConfig:
    """Return BuildConfig"""
    return BuildConfig(
        zephyr_base='zephyr',
        source_dir='source',
        build_dir=tmpdir_factory.mktemp('build'),
        output_dir=tmpdir_factory.mktemp('output'),
        platform_name='native_posix',
        platform_arch='',  # TODO:
        scenario='bt',
        cmake_filter='',
        cmake_extra_args=['-DCONF_FILE=prj_single.conf']
    )


@pytest.fixture
def west_builder(build_config) -> WestBuilder:
    """Return WestBuilder"""
    return WestBuilder(build_config)


@pytest.fixture
def cmake_builder(build_config) -> CMakeBuilder:
    """Return CMakeBuilder"""
    return CMakeBuilder(build_config)

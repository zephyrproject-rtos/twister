import pytest

from twister2.builder.builder_abstract import BuildConfig
from twister2.builder.cmake_builder import CmakeBuilder
from twister2.builder.west_builder import WestBuilder


@pytest.fixture
def build_config(tmp_path) -> BuildConfig:
    """Return BuildConfig"""
    return BuildConfig(
        zephyr_base='zephyr',
        source_dir='source',
        build_dir='build',
        output_dir=tmp_path,
        platform_name='native_posix',
        platform_arch='',  # TODO:
        scenario='bt',
        kconfig_dts_filter='',
        extra_args_spec=['CONF_FILE=prj_single.conf']
    )


@pytest.fixture
def west_builder(build_config) -> WestBuilder:
    """Return WestBuilder"""
    return WestBuilder(build_config)


@pytest.fixture
def cmake_builder(build_config) -> CmakeBuilder:
    """Return CmakeBuilder"""
    return CmakeBuilder(build_config)

import pytest

from twister2.builder.builder_abstract import BuildConfig


@pytest.fixture(name='build_config')
def fixture_build_config() -> BuildConfig:
    return BuildConfig(
        zephyr_base='zephyr',
        source_dir='source',
        build_dir='build',
        platform='native_posix',
        scenario='bt',
        extra_args=['CONFIG_NEWLIB_LIBC=y']
    )

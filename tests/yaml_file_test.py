from pathlib import Path

import pytest

from twister2.platform_specification import PlatformSpecification
from twister2.twister_config import TwisterConfig
from twister2.yaml_file import (
    _join_filters,
    _join_strings,
    _read_test_specifications_from_yaml,
    should_skip_for_arch,
    should_skip_for_min_flash,
    should_skip_for_min_ram,
    should_skip_for_platform,
    should_skip_for_tag,
    should_skip_for_toolchain,
    should_skip_for_unsupported_harness,
)
from twister2.yaml_test_specification import YamlTestSpecification

DATA_DIR: Path = Path(__file__).parent / 'data'


@pytest.fixture(scope='function')
def testcase() -> YamlTestSpecification:
    return YamlTestSpecification(
        name='dummy_test',
        original_name='dummy_test',
        rel_to_base_path=Path('out_of_tree'),
        platform='platform',
        source_dir=Path('dummy_path')
    )


@pytest.fixture(scope='function')
def platform() -> PlatformSpecification:
    return PlatformSpecification(identifier='platform_xyz')


@pytest.fixture(scope='function')
def twister_config(platform) -> TwisterConfig:
    return TwisterConfig(
        zephyr_base='dummy_path',
        default_platforms=[platform.identifier],
        platforms=[platform]
    )


def test_should_skip_for_tag_for_only_tags_positive(testcase, platform):
    testcase.tags = {'tag1', 'tag2'}
    platform.only_tags = ['tag3', 'tag4']
    assert should_skip_for_tag(testcase, platform)


def test_should_skip_for_tag_for_only_tags_negative(testcase, platform):
    testcase.tags = {'tag1', 'tag2'}
    platform.only_tags = ['tag1', 'tag4']
    assert should_skip_for_tag(testcase, platform) is False


def test_should_skip_for_tag_for_ignore_tags_positive(testcase, platform):
    testcase.tags = {'tag1', 'tag2'}
    platform.ignore_tags = ['tag1', 'tag4']
    assert should_skip_for_tag(testcase, platform)


def test_should_skip_for_tag_for_ignore_tags_negative(testcase, platform):
    testcase.tags = {'tag1', 'tag2'}
    platform.ignore_tags = ['tag3', 'tag4']
    assert should_skip_for_tag(testcase, platform) is False


def test_should_skip_for_arch_for_arch_allow_positive(testcase, platform):
    testcase.arch_allow = {'arch1', 'arch2'}
    platform.arch = 'arch3'
    assert should_skip_for_arch(testcase, platform)


def test_should_skip_for_arch_for_arch_allow_negative(testcase, platform):
    testcase.arch_allow = {'arch1', 'arch2'}
    platform.arch = 'arch1'
    assert should_skip_for_arch(testcase, platform) is False


def test_should_skip_for_arch_for_arch_exclude_positive(testcase, platform):
    testcase.arch_exclude = {'arch1', 'arch2'}
    platform.arch = 'arch1'
    assert should_skip_for_arch(testcase, platform)


def test_should_skip_for_arch_for_arch_exclude_negative(testcase, platform):
    testcase.arch_exclude = {'arch3', 'arch2'}
    platform.arch = 'arch1'
    assert should_skip_for_arch(testcase, platform) is False


def test_should_skip_for_toolchain_for_toolchain_allow_positive(testcase, platform):
    testcase.toolchain_allow = {'toolchain1'}
    platform.toolchain = ['toolchain2']
    assert should_skip_for_toolchain(testcase, platform)


def test_should_skip_for_toolchain_for_toolchain_allow_negative(testcase, platform):
    testcase.toolchain_allow = {'toolchain1'}
    platform.toolchain = ['toolchain1']
    assert should_skip_for_toolchain(testcase, platform) is False


def test_should_skip_for_toolchain_for_toolchain_exclude_positive(testcase, platform):
    testcase.toolchain_exclude = {'toolchain1', 'toolchain2'}
    platform.toolchain = ['toolchain2']
    assert should_skip_for_toolchain(testcase, platform)


def test_should_skip_for_toolchain_for_toolchain_exclude_negative(testcase, platform):
    testcase.toolchain_exclude = {'toolchain2'}
    platform.toolchain = ['toolchain1']
    assert should_skip_for_toolchain(testcase, platform) is False


def test_should_skip_for_platform_positive(testcase, platform):
    testcase.platform_allow = {'platform3', 'platform2'}
    platform.identifier = 'platform1'
    assert should_skip_for_platform(testcase, platform)


def test_should_skip_for_platform_negative(testcase, platform):
    testcase.platform_allow = {'platform1', 'platform2'}
    platform.identifier = 'platform1'
    assert should_skip_for_platform(testcase, platform) is False


def test_should_skip_for_platform_for_platform_exclude_positive(testcase, platform):
    testcase.platform_exclude = {'platform1', 'platform2'}
    platform.identifier = 'platform1'
    assert should_skip_for_platform(testcase, platform)


def test_should_skip_for_platform_for_platform_exclude_negative(testcase, platform):
    testcase.platform_exclude = {'platform3', 'platform2'}
    platform.identifier = 'platform1'
    assert should_skip_for_platform(testcase, platform) is False


def test_should_skip_for_min_ram_negative(testcase, platform):
    testcase.min_ram = 200
    platform.ram = 100
    assert should_skip_for_min_ram(testcase, platform)


def test_should_skip_for_min_ram_positive(testcase, platform):
    testcase.min_ram = 200
    platform.ram = 300
    assert should_skip_for_min_ram(testcase, platform) is False


def test_should_skip_for_min_flash_negative(testcase, platform):
    testcase.min_flash = 200
    platform.flash = 100
    assert should_skip_for_min_flash(testcase, platform)


def test_should_skip_for_min_flash_positive(testcase, platform):
    testcase.min_flash = 200
    platform.flash = 300
    assert should_skip_for_min_flash(testcase, platform) is False


def test_should_skip_for_unsupported_platform_negative(testcase, platform):
    testcase.harness = 'pytest'
    assert should_skip_for_unsupported_harness(testcase, platform)


def test_should_skip_for_unsupported_platform_positive(testcase, platform):
    testcase.harness = 'console'
    assert should_skip_for_unsupported_harness(testcase, platform) is False


def test_if_join_strings_returns_joined_strings():
    assert _join_strings(['aaa', 'bbb']) == 'aaa bbb'


def test_if_join_strings_returns_joined_strings_without_empty_strings():
    assert _join_strings(['aaa', '', 'bbb', '']) == 'aaa bbb'


def test_if_join_filters_returns_joined_filters():
    assert _join_filters(['aaa', 'bbb']) == '(aaa) and (bbb)'


def test_if_join_filters_returns_joined_filters_without_empty_strings():
    assert _join_filters(['aaa', '', '', 'bbb']) == '(aaa) and (bbb)'


def test_read_test_specifications_from_yaml_common(twister_config):
    yaml_file_path = DATA_DIR / 'common' / 'testcase.yaml'
    for spec in _read_test_specifications_from_yaml(yaml_file_path, twister_config):
        if spec.original_name == 'xyz.common_merge_1':
            assert spec.tags == {'kernel', 'posix', 'picolibc'}
            assert spec.extra_configs == ['CONFIG_NEWLIB_LIBC=y', 'CONFIG_POSIX_API=y']
            assert spec.filter == '(CONFIG_PICOLIBC_SUPPORTED) and (TOOLCHAIN_HAS_NEWLIB == 1)'
            assert spec.min_ram == 64
        elif spec.original_name == 'xyz.common_merge_2':
            assert spec.tags == {'kernel', 'posix', 'arm'}
            assert spec.extra_configs == ['CONFIG_POSIX_API=y']
            assert spec.filter == 'TOOLCHAIN_HAS_NEWLIB == 1'
            assert spec.min_ram == 32

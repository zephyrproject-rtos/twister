from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from unittest import mock

import pytest

from twister2.specification_processor import (
    _join_filters,
    _join_strings,
    is_runnable,
    should_skip_for_arch,
    should_skip_for_depends_on,
    should_skip_for_min_flash,
    should_skip_for_min_ram,
    should_skip_for_platform,
    should_skip_for_platform_type,
    should_skip_for_pytest_harness,
    should_skip_for_spec_type_unit,
    should_skip_for_tag,
    should_skip_for_toolchain,
)
from twister2.yaml_test_specification import YamlTestSpecification


@pytest.fixture(scope='function')
def testcase() -> YamlTestSpecification:
    return YamlTestSpecification(
        name='dummy_test',
        original_name='dummy_test',
        rel_to_base_path=Path('out_of_tree'),
        platform='platform',
        source_dir=Path('dummy_path')
    )


def test_should_skip_for_spec_type_unit_positive(testcase, platform):
    testcase.type = "unit"
    assert should_skip_for_spec_type_unit(testcase, platform)


def test_should_skip_for_spec_type_unit_negative(testcase, platform):
    testcase.type = ""
    assert should_skip_for_spec_type_unit(testcase, platform) is False


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


def test_should_skip_for_platform_type_positive(testcase, platform):
    testcase.platform_type = {'mcu', 'native'}
    platform.identifier = 'mcu'
    assert should_skip_for_platform_type(testcase, platform)


def test_should_skip_for_platform_type_negative(testcase, platform):
    testcase.platform_allow = {'mcu', 'native'}
    platform.identifier = 'qemu'
    assert should_skip_for_platform_type(testcase, platform) is False


def test_should_skip_for_platform_for_platform_exclude_positive(testcase, platform):
    testcase.platform_exclude = {'platform1', 'platform2'}
    platform.identifier = 'platform1'
    assert should_skip_for_platform(testcase, platform)


def test_should_skip_for_platform_for_platform_exclude_negative(testcase, platform):
    testcase.platform_exclude = {'platform3', 'platform2'}
    platform.identifier = 'platform1'
    assert should_skip_for_platform(testcase, platform) is False


def test_should_skip_for_harness_pytest_positive(testcase, platform):
    testcase.harness = 'pytest'
    assert should_skip_for_pytest_harness(testcase, platform)


def test_should_skip_for_harness_pytest_negative(testcase, platform):
    testcase.harness = 'ztest'
    assert should_skip_for_pytest_harness(testcase, platform) is False


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


def test_should_skip_for_depends_on_negative(testcase, platform):
    testcase.depends_on = {'spi'}
    platform.supported = {'gpio'}
    assert should_skip_for_depends_on(testcase, platform)


def test_should_skip_for_depends_on_positive(testcase, platform):
    testcase.depends_on = {'spi'}
    platform.supported = {'gpio', 'spi'}
    assert should_skip_for_depends_on(testcase, platform) is False


@pytest.mark.parametrize('in_put,out_put', [
    ([], ''),
    (['aaa'], 'aaa'),
    (['aaa', 'bbb'], 'aaa bbb'),
    (['aaa', '', 'bbb', ''], 'aaa bbb'),
])
def test_if_join_strings_returns_joined_strings(in_put, out_put):
    assert _join_strings(in_put) == out_put


@pytest.mark.parametrize('in_put,out_put', [
    ([], ''),
    (['aaa'], 'aaa'),
    (['aaa', 'bbb'], '(aaa) and (bbb)'),
    (['aaa', '', '', 'bbb'], '(aaa) and (bbb)'),
])
def test_if_join_filters_returns_joined_filters(in_put, out_put):
    assert _join_filters(in_put) == out_put


@dataclass
class MockSpecification:
    harness: str = 'console'
    harness_config: dict = field(default_factory=dict)
    type: str = 'unit'
    build_only: bool = False


@dataclass
class MockPlatform:
    type: str = 'native'
    simulation: str = 'nsim'
    simulation_exec: str = ''


@pytest.mark.parametrize(
    'spec,platform,fixtures',
    [
        (MockSpecification(), MockPlatform(), []),
        (MockSpecification(), MockPlatform(simulation_exec='na'), []),
        (MockSpecification(), MockPlatform(), None),
        (MockSpecification(type='unit'), MockPlatform(type='nsim', simulation='not-supported'), []),
        (MockSpecification(type='mcu'), MockPlatform(type='native', simulation='not-supported'), []),
        (MockSpecification(), MockPlatform(simulation_exec='python'), []),
        (MockSpecification(harness_config=dict(fixture='fixture_display')), MockPlatform(), ['fixture_display']),
        (MockSpecification(), MockPlatform(), ['fixture_display']),
        (MockSpecification(type='integration'), MockPlatform(type='mcu', simulation='na'), []),  # test on hardware
    ]
)
def test_if_test_is_runnable(spec, platform, fixtures):
    with mock.patch('os.name', 'linux'):
        assert is_runnable(spec, platform, fixtures)  # type: ignore


@pytest.mark.parametrize(
    'spec,platform,fixtures',
    [
        (MockSpecification(harness='keyboard'), MockPlatform(), []),  # not supported harness
        # not supported target type:
        (MockSpecification(type='integration'), MockPlatform(type='sim', simulation='not-supported'), []),
        (MockSpecification(), MockPlatform(simulation_exec='dummy'), []),  # tool not installed
        (MockSpecification(harness_config=dict(fixture='fixture_display')), MockPlatform(), []),  # fixture not match
        (MockSpecification(harness_config=dict(fixture='fixture_ppk')), MockPlatform(), ['fixture_display']),
    ]
)
def test_if_test_is_not_runnable(spec, platform, fixtures):
    with mock.patch('os.name', 'linux'):
        assert is_runnable(spec, platform, fixtures) is False  # type: ignore


def test_if_test_is_not_runnable_on_windows():
    with mock.patch('os.name', 'nt'):
        assert is_runnable(MockSpecification(), MockPlatform(), []) is False  # type: ignore

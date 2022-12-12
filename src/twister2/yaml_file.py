"""
Module is responsible for searching and parsing yaml files, and generating test cases.

Base of non-python test definition:
https://github.com/pytest-dev/pytest/issues/3639
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

import pytest

from twister2.helper import safe_load_yaml
from twister2.platform_specification import PlatformSpecification
from twister2.twister_config import TwisterConfig
from twister2.yaml_test_function import YamlTestFunction, yaml_test_function_factory
from twister2.yaml_test_specification import (
    YamlTestSpecification,
    validate_test_specification_data,
)

logger = logging.getLogger(__name__)


class YamlFile(pytest.File):
    """Class for collecting tests from a yaml file."""

    def collect(self):
        """Return a list of yaml tests."""
        twister_config = self.config.twister_config
        # read all tests from yaml file and generate pytest test functions
        for spec in _read_test_specifications_from_yaml(self.path, twister_config):
            test_function: YamlTestFunction = yaml_test_function_factory(spec=spec, parent=self)
            yield test_function


def _generate_test_variants_for_platforms(
    spec: dict, twister_config: TwisterConfig
) -> Generator[YamlTestSpecification, None, None]:
    """Generate test variants according to provided platforms."""
    assert isinstance(twister_config, TwisterConfig)
    spec = spec.copy()

    platforms = [
        platform for platform in twister_config.platforms
        if platform.identifier in twister_config.default_platforms
    ]

    test_name = spec['name']
    for platform in platforms:
        spec['name'] = f'{test_name}[{platform.identifier}]'
        spec['original_name'] = test_name
        spec['platform'] = platform.identifier
        yaml_test_spec = YamlTestSpecification(**spec)

        if should_be_skip(yaml_test_spec, platform):
            continue

        logger.debug('Generated test %s for platform %s', test_name, platform.identifier)
        yield yaml_test_spec


def _read_test_specifications_from_yaml(
    filepath: Path, twister_config: TwisterConfig
) -> Generator[YamlTestSpecification, None, None]:
    """
    Return generator of yaml test specifications.

    :param filepath: path to a yaml file
    :param twister_config: twister configuration
    :return: generator of yaml test specifications
    """
    yaml_tests: dict = safe_load_yaml(filepath)
    if yaml_tests.get('tests') is None:
        return

    yaml_tests = extract_tests(yaml_tests)

    for test_name, spec in yaml_tests.items():
        test_name: str  # type: ignore
        spec: dict  # type: ignore
        spec['name'] = test_name
        spec['source_dir'] = Path(filepath).parent
        try:
            spec['rel_to_base_path'] = Path.relative_to(spec['source_dir'], twister_config.zephyr_base)
        except ValueError:
            # Test not in zephyr tree
            spec['rel_to_base_path'] = 'out_of_tree'

        for test_spec in _generate_test_variants_for_platforms(spec, twister_config):
            yield test_spec


def extract_tests(raw_spec: dict) -> dict:
    validate_test_specification_data(raw_spec)
    sample = raw_spec.get('sample', {})  # exists in yaml, but it is not used # noqa: F841
    common = raw_spec.get('common', {})

    tests: dict = {}
    for test_name, test_spec_dict in raw_spec['tests'].items():

        for key, common_value in common.items():
            if key in test_spec_dict:
                if key == 'filter':
                    test_spec_dict[key] = _join_filters([test_spec_dict[key], common_value])
                elif isinstance(common_value, str):
                    test_spec_dict[key] = _join_strings([test_spec_dict[key], common_value])
                elif isinstance(common_value, list):
                    test_spec_dict[key] = test_spec_dict[key] + common_value
                else:
                    # if option in spec already exists and does not cover above
                    # mentioned cases - leave it as is
                    pass
            else:
                test_spec_dict[key] = common_value
        tests[test_name] = test_spec_dict

    return tests


def _join_filters(args: list[str]) -> str:
    assert all(isinstance(arg, str) for arg in args)
    if len(args) == 1:
        return args[0]
    args = [f'({arg})' for arg in args if arg]
    return ' and '.join(args)


def _join_strings(args: list[str]) -> str:
    assert all(isinstance(arg, str) for arg in args)
    # remove empty strings
    args = [arg for arg in args if arg]
    return ' '.join(args)


def _log_test_skip(test_spec: YamlTestSpecification, platform: PlatformSpecification, reason: str) -> None:
    testcases_logger = logging.getLogger('testcases')  # it logs only to file
    testcases_logger.info(
        'Skipped test %s for platform %s - %s',
        test_spec.original_name, platform.identifier, reason
    )


def should_be_skip(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    """
    Return True if given test spec should be skipped for the platform.

    :param test_spec: test specification
    :param platform: platform specification
    :return: True is the specification should be skipped
    """
    if any([
        should_skip_for_arch(test_spec, platform),
        should_skip_for_min_flash(test_spec, platform),
        should_skip_for_min_ram(test_spec, platform),
        should_skip_for_platform(test_spec, platform),
        should_skip_for_platform_type(test_spec, platform),
        should_skip_for_tag(test_spec, platform),
        should_skip_for_toolchain(test_spec, platform),
    ]):
        return True
    # TODO:
    # filter by build_on_all
    return False


def should_skip_for_toolchain(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if not platform.toolchain:
        return False
    if test_spec.toolchain_allow and not test_spec.toolchain_allow & set(platform.toolchain):
        _log_test_skip(test_spec, platform, 'platform.toolchain not in testcase.toolchain_allow')
        return True
    if test_spec.toolchain_exclude and test_spec.toolchain_exclude & set(platform.toolchain):
        _log_test_skip(test_spec, platform, 'platform.toolchain in testcase.toolchain_exclude')
        return True
    return False


def should_skip_for_tag(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if platform.only_tags and not set(platform.only_tags) & test_spec.tags:
        _log_test_skip(test_spec, platform, 'testcase.tag not in platform.only_tags')
        return True
    if platform.ignore_tags and set(platform.ignore_tags) & test_spec.tags:
        _log_test_skip(test_spec, platform, 'testcase.tag in platform.ignore_tags')
        return True
    return False


def should_skip_for_arch(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if test_spec.arch_allow and platform.arch not in test_spec.arch_allow:
        _log_test_skip(test_spec, platform, 'platform.arch not in testcase.arch_allow')
        return True
    if test_spec.arch_exclude and platform.arch in test_spec.arch_exclude:
        _log_test_skip(test_spec, platform, 'platform.arch in testcase.arch_exclude')
        return True
    return False


def should_skip_for_platform(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if test_spec.platform_allow and platform.identifier not in test_spec.platform_allow:
        _log_test_skip(test_spec, platform, 'platform.identifier not in testcase.platform_allow')
        return True
    if test_spec.platform_exclude and platform.identifier in test_spec.platform_exclude:
        _log_test_skip(test_spec, platform, 'platform.identifier in testcase.platform_exclude')
        return True
    return False


def should_skip_for_platform_type(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if test_spec.platform_type and platform.type not in test_spec.platform_type:
        _log_test_skip(test_spec, platform, 'platform.type not in testcase.platform_type')
        return True
    return False


def should_skip_for_min_ram(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if test_spec.min_ram > platform.ram:
        _log_test_skip(test_spec, platform, 'platform.ram is less than testcase.min_ram')
        return True
    return False


def should_skip_for_min_flash(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if test_spec.min_flash > platform.flash:
        _log_test_skip(test_spec, platform, 'platform.flash is less than testcase.min_flash')
        return True
    return False

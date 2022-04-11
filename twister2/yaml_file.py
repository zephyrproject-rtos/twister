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
import yaml

from twister2.twister_config import TwisterConfig
from twister2.yaml_test_function import YamlTestFunction, yaml_test_function_factory
from twister2.yaml_test_specification import YamlTestSpecification

logger = logging.getLogger(__name__)


class YamlFile(pytest.File):
    """Class for collecting tests from a yaml file."""

    def collect(self):
        """Return a list of yaml tests."""
        twister_config = self.config.twister_config
        # read all tests from yaml file and generate pytest test functions
        for spec in _read_test_specifications_from_yaml(self.fspath, twister_config):
            test_function: YamlTestFunction = yaml_test_function_factory(spec=spec, parent=self)
            # extend xml report
            test_function.user_properties.append(('type', spec.type))
            test_function.user_properties.append(('tags', ' '.join(spec.tags)))
            test_function.user_properties.append(('platform', spec.platform))
            yield test_function


def _generate_test_variants_for_platforms(
    spec: dict, twister_config: TwisterConfig
) -> Generator[YamlTestSpecification, None, None]:
    """Generate test variants according to provided platforms."""
    assert isinstance(twister_config, TwisterConfig)
    spec = spec.copy()
    default_platforms = twister_config.default_platforms

    allowed_platform = spec.get('allowed_platform', '').split() or default_platforms
    platform_exclude = spec.get('platform_exclude', '').split()
    test_name = spec['name']

    logger.debug('Generating tests for %s with selected platforms %s', test_name, default_platforms)

    for platform in allowed_platform:
        if platform in platform_exclude:
            continue
        spec['name'] = test_name + f'[{platform}]'
        spec['original_name'] = test_name
        spec['platform'] = platform
        yaml_test_spec = YamlTestSpecification(**spec)
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
    yaml_tests: dict = yaml.safe_load(filepath.open())
    if yaml_tests.get('tests') is None:
        return

    sample = yaml_tests.get('sample', {})  # exists in yaml, but it is not used # noqa: F841
    common = yaml_tests.get('common', {})

    for test_name, spec in yaml_tests['tests'].items():
        test_name: str  # type: ignore
        spec: dict  # type: ignore

        for key, value in spec.items():
            common_value = common.pop(key, None)
            if not common_value:
                continue
            if key == 'filter':
                spec[key] = _join_filters([spec[key], common_value])
                continue
            if isinstance(value, str):
                spec[key] = _join_strings([spec[key], common_value])
                continue
            if isinstance(value, list):
                spec[key] = spec[key] + common_value
                continue

        spec.update(common)
        spec['name'] = test_name
        spec['path'] = Path(filepath).parent

        for test_spec in _generate_test_variants_for_platforms(spec, twister_config):
            yield test_spec


def _join_filters(args: list[str]) -> str:
    assert all(isinstance(arg, str) for arg in args)
    if len(args) == 1:
        return args[0]
    args = [f'({arg})' for arg in args if args]
    return ' and '.join(args)


def _join_strings(args: list[str]) -> str:
    assert all(isinstance(arg, str) for arg in args)
    # remove empty strings
    args = [arg for arg in args if args]
    return ' '.join(args)

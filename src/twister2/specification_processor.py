from __future__ import annotations

import abc
import logging
import math
import os
import shutil
from pathlib import Path

import pytest

from twister2.exceptions import TwisterConfigurationException
from twister2.helper import safe_load_yaml
from twister2.platform_specification import PlatformSpecification
from twister2.yaml_test_function import add_markers_from_specification
from twister2.yaml_test_specification import (
    SUPPORTED_HARNESSES,
    YamlTestSpecification,
    validate_test_specification_data,
)

TEST_SPEC_FILE_NAME: str = 'testspec.yaml'
SUPPORTED_SIMS: list[str] = ['mdb-nsim', 'nsim', 'renode', 'qemu', 'tsim', 'armfvp', 'xt-sim', 'native']

logger = logging.getLogger(__name__)


class SpecificationProcessor(abc.ABC):
    """Prepars specification for test"""

    def __init__(self, twister_config):
        self.twister_config = twister_config

    @abc.abstractmethod
    def process(self, platform: PlatformSpecification, scenario: str) -> YamlTestSpecification | None:
        """Create yaml specification for platform and scenario."""

    def create_spec_from_dict(self, test_spec_dict: dict, platform: PlatformSpecification) -> YamlTestSpecification:
        test_spec = YamlTestSpecification(**test_spec_dict)
        test_spec.timeout = math.ceil(test_spec.timeout * platform.testing.timeout_multiplier)
        test_spec.runnable = is_runnable(test_spec, platform, self.twister_config.fixtures)
        return test_spec


class YamlSpecificationProcessor(SpecificationProcessor):
    """Specification processor class for twister tests."""

    def __init__(self, twister_config, filepath: Path) -> None:
        super().__init__(twister_config)
        self.spec_file_path = filepath
        self.zephyr_base: str = self.twister_config.zephyr_base
        self.test_directory_path: Path = self.spec_file_path.parent
        self.raw_spec: dict = safe_load_yaml(self.spec_file_path)
        self.tests: dict = extract_tests(self.raw_spec)
        self.scenarios: list[str] = list(self.tests.keys())

    def prepare_spec_dict(self, platform: PlatformSpecification, scenario: str) -> dict:
        try:
            test_spec_dict = self.tests[scenario]
        except KeyError:
            msg = f'There is no specification for {scenario} in file {self.spec_file_path}'
            logger.error(msg)
            raise TwisterConfigurationException(msg)

        test_spec_dict['name'] = f'{scenario}[{platform.identifier}]'
        test_spec_dict['original_name'] = scenario
        test_spec_dict['platform'] = platform.identifier
        test_spec_dict['source_dir'] = self.test_directory_path
        try:
            test_spec_dict['rel_to_base_path'] = Path.relative_to(test_spec_dict['source_dir'], self.zephyr_base)
        except ValueError:
            # Test not in zephyr tree
            test_spec_dict['rel_to_base_path'] = 'out_of_tree'

        return test_spec_dict

    def process(  # type: ignore[return]
        self, platform: PlatformSpecification, scenario: str
    ) -> YamlTestSpecification | None:
        test_spec_dict = self.prepare_spec_dict(platform, scenario)
        test_spec = self.create_spec_from_dict(test_spec_dict, platform)
        if not should_be_skip(test_spec, platform):
            logger.debug('Generated test %s for platform %s', scenario, platform.identifier)
            return test_spec


class RegularSpecificationProcessor(SpecificationProcessor):
    """Specification processor class for regular pytest tests."""

    def __init__(self, twister_config, item: pytest.Item) -> None:
        super().__init__(twister_config)
        self.item = item
        self.config = self.item.config
        self.rootpath = self.config.rootpath
        self.test_directory_path: Path = self.item.path.parent
        self.spec_file_path: Path = self.test_directory_path.joinpath(TEST_SPEC_FILE_NAME)
        assert self.spec_file_path.exists(), f'Spec file does not exist: {self.spec_file_path}'
        self.raw_spec = safe_load_yaml(self.spec_file_path)
        self.tests = extract_tests(self.raw_spec)

    def process(self, platform: PlatformSpecification, scenario: str) -> YamlTestSpecification | None:
        test_spec_dict = self.prepare_spec_dict(platform, scenario)
        test_spec = self.create_spec_from_dict(test_spec_dict, platform)
        add_markers_from_specification(self.item, test_spec)
        if should_be_skip(test_spec, platform):
            self.item.add_marker(pytest.mark.skip('Does not match requirements'))

        return test_spec

    def prepare_spec_dict(self, platform: PlatformSpecification, scenario: str) -> dict:
        try:
            test_spec_dict = self.tests[scenario]
        except KeyError:
            msg = f'There is no specification for {scenario} in file {self.spec_file_path}'
            logger.error(msg)
            raise TwisterConfigurationException(msg)

        test_spec_dict['name'] = self.item.name
        test_spec_dict['original_name'] = self.item.originalname  # type: ignore[attr-defined]
        test_spec_dict['source_dir'] = self.test_directory_path
        test_spec_dict['platform'] = platform.identifier
        test_spec_dict['build_name'] = scenario
        test_spec_dict['rel_to_base_path'] = Path.relative_to(test_spec_dict['source_dir'], self.rootpath)
        return test_spec_dict


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
    # TODO: Implement #1 #13
    if any([
        should_skip_for_arch(test_spec, platform),
        should_skip_for_min_flash(test_spec, platform),
        should_skip_for_min_ram(test_spec, platform),
        should_skip_for_platform(test_spec, platform),
        should_skip_for_platform_type(test_spec, platform),
        should_skip_for_pytest_harness(test_spec, platform),
        should_skip_for_tag(test_spec, platform),
        should_skip_for_toolchain(test_spec, platform),
    ]):
        return True
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


def should_skip_for_pytest_harness(test_spec: YamlTestSpecification, platform: PlatformSpecification) -> bool:
    if test_spec.harness == 'pytest':
        _log_test_skip(test_spec, platform, 'test harness "pytest" is natively supported by pytest')
        return True
    return False


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


def is_runnable(
    spec: YamlTestSpecification,
    platform: PlatformSpecification,
    fixtures: list[str] | None = None
) -> bool:
    """
    Return if test can be executed on current setup.

    :param spec: test specification
    :param platform: selected platform
    :param fixtures: list of additional devices connected to the test setup
    :return: True if test is runnable
    """
    if os.name == 'nt' and platform.simulation != 'na':
        logger.debug('Simulators not supported on Windows')
        return False

    if spec.harness not in SUPPORTED_HARNESSES:
        logger.debug(f'Harness is not supported {spec.harness}')
        return False

    if not any([
        spec.type == 'unit',
        platform.type in ['native', 'mcu'],
        platform.simulation in SUPPORTED_SIMS
    ]):
        logger.debug(f'Target type not supported: {platform.type}')
        return False

    for sim in ['nsim', 'mdb-nsim', 'renode', 'tsim', 'native']:
        if platform.simulation == sim and platform.simulation_exec and platform.simulation_exec != 'na':
            if shutil.which(platform.simulation_exec) is None:
                logger.debug(f'{platform.simulation_exec} not found.')
                return False

    if fixtures is None:
        fixtures = []
    if (fixture := spec.harness_config.get('fixture')) and fixture not in fixtures:
        logger.debug('Required fixture {fixture} is not available')
        return False

    return True

"""
Plugin generates variants of tests bases on specification from YAML file.
Test variants are generated for `platform` and `scenario`.
"""

from __future__ import annotations

import itertools
import logging
import math
from dataclasses import dataclass
from pathlib import Path

import pytest

from twister2.exceptions import TwisterConfigurationException
from twister2.helper import safe_load_yaml
from twister2.platform_specification import PlatformSpecification
from twister2.yaml_file import extract_tests, should_be_skip
from twister2.yaml_test_function import add_markers_from_specification
from twister2.yaml_test_specification import YamlTestSpecification

TEST_SPEC_FILE_NAME = 'testspec.yaml'

logger = logging.getLogger(__name__)


@dataclass
class Variant:
    """Keeps information about single test variant"""
    platform: PlatformSpecification
    scenario: str

    def __str__(self):
        return f'{self.platform.identifier}:{self.scenario}'


def get_scenarios_from_fixture(metafunc: pytest.Metafunc) -> list[str]:
    """Return scenarios selected by fixture `build_specification`."""
    if mark := metafunc.definition.get_closest_marker('build_specification'):
        scenarios = list(mark.args)
        if not scenarios:
            logger.warning(
                'At least one `scenario` should be added to `build_specification` decorator in test: %s',
                metafunc.definition.nodeid
            )
        return scenarios
    return []


def get_scenarios_from_yaml(spec_file: Path) -> list[str]:
    """Return all available scenarios from yaml specification."""
    data = safe_load_yaml(spec_file)
    try:
        return data['tests'].keys()
    except KeyError:
        return []


def pytest_generate_tests(metafunc: pytest.Metafunc):
    # generate parametrized tests for each selected platform for ordinary pytest tests
    # if `specification` fixture is used
    if 'specification' not in metafunc.fixturenames:
        return

    twister_config = metafunc.config.twister_config

    platforms_list: list[PlatformSpecification] = [
        platform for platform in twister_config.platforms
        if platform.identifier in twister_config.default_platforms
    ]
    spec_file_path: Path = Path(metafunc.definition.fspath.dirname) / TEST_SPEC_FILE_NAME
    scenarios = get_scenarios_from_fixture(metafunc)
    assert spec_file_path.exists(), f'There is no specification file for the test: {spec_file_path}'
    if not scenarios:
        scenarios = get_scenarios_from_yaml(spec_file_path)
    variants = itertools.product(platforms_list, scenarios)
    params: list[pytest.param] = []
    for variant in variants:
        v = Variant(*variant)
        params.append(
            pytest.param(v, marks=pytest.mark.platform(v.platform.identifier), id=str(v))
        )

    # using indirect=True to inject value from `specification` fixture instead of param
    metafunc.parametrize(
        'specification', params, scope='function', indirect=True
    )


@pytest.fixture(scope='function')
def specification() -> None:
    """Injects a test specification from yaml file to a test item"""
    # The body of this function is empty because it is only used to
    # inform pytest that we want to generate parametrized tests for
    # a test function which uses this fixture


def pytest_configure(config: pytest.Config):
    config.addinivalue_line(
        'markers', 'build_specification(names="scenario1,scenario2"): select scenarios to build'
    )


def generate_yaml_test_specification_for_item(item: pytest.Item, variant: Variant) -> YamlTestSpecification:
    """Add test specification from yaml file to test item."""
    logger.debug('Adding test specification to item "%s"', item.nodeid)
    scenario: str = variant.scenario
    platform: PlatformSpecification = variant.platform

    spec_path: Path = item.path.parent.joinpath(TEST_SPEC_FILE_NAME)
    assert spec_path.exists(), f'Spec file does not exist: {spec_path}'
    test_directory_path: Path = item.path.parent
    rootpath: Path = item.config.rootpath

    raw_spec: dict = safe_load_yaml(spec_path)
    tests: dict = extract_tests(raw_spec)

    try:
        test_spec_dict = tests[scenario]
    except KeyError:
        msg = f'There is no specification for {scenario} in file {spec_path}'
        logger.error(msg)
        raise TwisterConfigurationException(msg)

    test_spec_dict['name'] = item.name
    test_spec_dict['original_name'] = item.originalname
    test_spec_dict['source_dir'] = test_directory_path
    test_spec_dict['platform'] = platform.identifier
    test_spec_dict['build_name'] = scenario
    test_spec_dict['rel_to_base_path'] = Path.relative_to(test_spec_dict['source_dir'], rootpath)

    test_spec = YamlTestSpecification(**test_spec_dict)
    test_spec.timeout = math.ceil(test_spec.timeout * platform.testing.timeout_multiplier)

    add_markers_from_specification(item, test_spec)
    if should_be_skip(test_spec, platform):
        item.add_marker(pytest.mark.skip('Does not match requirements'))

    return test_spec


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
):
    if not hasattr(session, 'specifications'):
        session.specifications = {}

    for item in items:
        # add YAML test specification to session for consistency with python tests
        if hasattr(item.function, 'spec') and item.nodeid not in session.specifications:
            session.specifications[item.nodeid] = item.function.spec
        # yaml test function has no `callspec`
        if not hasattr(item, 'callspec'):
            continue
        if variant := item.callspec.params.get('specification'):
            spec = generate_yaml_test_specification_for_item(item, variant)
            session.specifications[item.nodeid] = spec

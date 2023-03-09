"""
Plugin generates variants of tests bases on specification from YAML file.
Test variants are generated for `platform` and `scenario`.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import pytest

from twister2.helper import safe_load_yaml
from twister2.platform_specification import PlatformSpecification
from twister2.specification_processor import (
    TEST_SPEC_FILE_NAME,
    RegularSpecificationProcessor,
)
from twister2.yaml_test_specification import YamlTestSpecification

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
        return list(mark.args)
    return []


def get_scenarios_from_yaml(spec_file: Path) -> list[str]:
    """Return all available scenarios from yaml specification."""
    data = safe_load_yaml(spec_file)
    try:
        return data['tests'].keys()
    except KeyError:
        return []


def generate_yaml_test_specification_for_item(item: pytest.Item, variant: Variant) -> YamlTestSpecification | None:
    """Add test specification from yaml file to test item."""
    logger.debug('Adding test specification to item "%s"', item.nodeid)
    scenario: str = variant.scenario
    platform: PlatformSpecification = variant.platform

    twister_config = item.config.twister_config  # type: ignore[attr-defined]
    processor = RegularSpecificationProcessor(twister_config, item)
    test_spec = processor.process(platform, scenario)
    return test_spec


class GenerateTestPlugin:

    @pytest.fixture(scope='function')
    def specification(self, request: pytest.FixtureRequest) -> YamlTestSpecification | None:
        """Return test specification from yaml file taking into account the appropriate platform and scenario."""
        if hasattr(request.session, 'specifications'):
            return request.session.specifications.get(request.node.nodeid)  # type: ignore[attr-defined]
        else:
            return None

    def pytest_generate_tests(self, metafunc: pytest.Metafunc):
        # generate parametrized tests for each selected platform for ordinary pytest tests
        # if `build_specification` marker is used
        if not metafunc.definition.get_closest_marker('build_specification'):
            return

        # inject fixture for parametrized tests
        if 'specification' not in metafunc.definition.fixturenames:
            metafunc.definition.fixturenames.append('specification')

        twister_config = metafunc.config.twister_config  # type: ignore[attr-defined]

        platforms_list: list[PlatformSpecification] = [
            platform for platform in twister_config.platforms
            if platform.identifier in twister_config.selected_platforms
        ]
        spec_file_path: Path = \
            Path(metafunc.definition.fspath.dirname) / TEST_SPEC_FILE_NAME  # type: ignore[attr-defined]
        scenarios = get_scenarios_from_fixture(metafunc)
        assert spec_file_path.exists(), f'There is no specification file for the test: {spec_file_path}'
        if not scenarios:
            scenarios = get_scenarios_from_yaml(spec_file_path)
        variants = itertools.product(platforms_list, scenarios)
        params: list[NamedTuple] = []
        for variant in variants:
            v = Variant(*variant)
            params.append(
                pytest.param(v, marks=pytest.mark.platform(v.platform.identifier), id=str(v))
            )

        # using indirect=True to inject value from `specification` fixture instead of param
        metafunc.parametrize(
            'specification', params, scope='function', indirect=True
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(
        self,
        session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ):
        if not hasattr(session, 'specifications'):
            session.specifications = {}  # type: ignore[attr-defined]

        for item in items:
            # add YAML test specification to session for consistency with python tests
            if all([
                hasattr(item.function, 'spec'),  # type: ignore[attr-defined]
                item.nodeid not in session.specifications   # type: ignore[attr-defined]
            ]):
                session.specifications[item.nodeid] = item.function.spec  # type: ignore[attr-defined]
            # yaml test function has no `callspec`
            if not hasattr(item, 'callspec'):
                continue
            if variant := item.callspec.params.get('specification'):
                if spec := generate_yaml_test_specification_for_item(item, variant):
                    session.specifications[item.nodeid] = spec  # type: ignore[attr-defined]

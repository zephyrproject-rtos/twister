"""
Plugin generates variants of tests bases on specification from YAML file.
Test variants are generated for `platform` and `scenario`.
"""

from __future__ import annotations

import logging
from typing import NamedTuple

import pytest

from twister2.specification_processor import RegularSpecificationProcessor
from twister2.yaml_test_function import add_markers_from_specification
from twister2.yaml_test_specification import YamlTestSpecification

logger = logging.getLogger(__name__)


def get_scenarios_from_fixture(metafunc: pytest.Metafunc) -> list[str]:
    """Return scenarios selected by fixture `build_specification`."""
    if mark := metafunc.definition.get_closest_marker('build_specification'):
        return list(mark.args)
    return []


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

        scenarios = get_scenarios_from_fixture(metafunc)
        processor = RegularSpecificationProcessor(twister_config, metafunc.definition)
        params: list[NamedTuple] = []
        for platform, scenario in processor.get_test_configurations():
            if scenarios and scenario not in scenarios:
                continue
            if test_spec := processor.process(platform, scenario):
                id_name = f'{platform.identifier}:{scenario}'
                params.append(
                    pytest.param(test_spec, id=id_name)
                )

        if params:
            # using indirect=True to inject value from `specification` fixture instead of param
            metafunc.parametrize(
                'specification', params, scope='function', indirect=True
            )

    def pytest_collection_modifyitems(
        self,
        session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ):
        if not hasattr(session, 'specifications'):
            session.specifications = {}  # type: ignore[attr-defined]

        items_to_remove = []
        for item in items:
            if item.nodeid in session.specifications:  # type: ignore[attr-defined]
                continue
            if hasattr(item, 'callspec'):  # type: ignore[attr-defined]
                if spec := item.callspec.params.get('specification'):  # type: ignore[attr-defined]
                    add_markers_from_specification(item, spec)
                    session.specifications[item.nodeid] = spec  # type: ignore[attr-defined]
                    config.twister_config.selected_platforms.add(  # type: ignore[attr-defined]
                        spec.platform
                    )
            # remove test with 'build_specification' marker, do not keep them as 'skipped'
            elif item.get_closest_marker('build_specification'):
                items_to_remove.append(item.nodeid)

        items[:] = [item for item in items if item.nodeid not in items_to_remove]

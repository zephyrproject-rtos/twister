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

from twister2.specification_processor import YamlSpecificationProcessor
from twister2.twister_config import TwisterConfig
from twister2.yaml_test_function import YamlFunction, yaml_test_function_factory
from twister2.yaml_test_specification import YamlTestSpecification

SAMPLE_FILENAME: str = 'sample.yaml'
TESTCASE_FILENAME: str = 'testcase.yaml'

logger = logging.getLogger(__name__)


class YamlPytestPlugin():

    def pytest_collect_file(self, parent, path):
        # discovers all yaml tests in test directory
        if path.basename in (SAMPLE_FILENAME, TESTCASE_FILENAME):
            return YamlModule.from_parent(parent, path=Path(path))

    def pytest_ignore_collect(self, path, config):
        if config.option.load_tests_path:
            return True
        elif config.option.only_from_yaml:
            if path.basename not in (SAMPLE_FILENAME, TESTCASE_FILENAME):
                return True
        return False

    def pytest_collection_modifyitems(
        self,
        session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ):
        if not hasattr(session, 'specifications'):
            session.specifications = {}  # type: ignore[attr-defined]

        for item in items:
            if item.nodeid in session.specifications:  # type: ignore[attr-defined]
                continue
            # add YAML test specification to session for consistency with python tests
            if hasattr(item.function, 'spec'):  # type: ignore[attr-defined]
                session.specifications[item.nodeid] = item.function.spec  # type: ignore[attr-defined]
                config.twister_config.selected_platforms.add(  # type: ignore[attr-defined]
                    item.function.spec.platform  # type: ignore[attr-defined]
                )


class YamlModule(pytest.File):
    """Class for collecting tests from a yaml file."""

    def collect(self) -> Generator[YamlFunction, None, None]:
        """Return a list of yaml tests."""
        twister_config = self.config.twister_config  # type: ignore
        # read all tests from yaml file and generate pytest test functions
        for spec in read_test_specifications_from_yaml(self.path, twister_config):
            test_function: YamlFunction = yaml_test_function_factory(spec=spec, parent=self)
            yield test_function


def read_test_specifications_from_yaml(
    filepath: Path, twister_config: TwisterConfig
) -> Generator[YamlTestSpecification, None, None]:
    """
    Return generator of yaml test specifications.

    :param filepath: path to a yaml file
    :param twister_config: twister configuration
    :return: generator of yaml test specifications
    """
    processor = YamlSpecificationProcessor(twister_config, filepath)

    for platform, scenario in processor.get_test_configurations():
        if test_spec := processor.process(platform, scenario):
            yield test_spec

"""
Module is responsible for searching and parsing yaml files, and generating test cases.

Base of non-python test definition:
https://github.com/pytest-dev/pytest/issues/3639
"""
from __future__ import annotations

import itertools
import logging
from pathlib import Path
from typing import Generator

import pytest

from twister2.specification_processor import YamlSpecificationProcessor
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
        for spec in read_test_specifications_from_yaml(self.path, twister_config):
            test_function: YamlTestFunction = yaml_test_function_factory(spec=spec, parent=self)
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
    processor = YamlSpecificationProcessor(filepath, twister_config.zephyr_base)

    platforms = (
        platform for platform in twister_config.platforms
        if platform.identifier in twister_config.default_platforms
    )
    scenarios: list[str] = processor.scenarios

    for platform, scenario in itertools.product(platforms, scenarios):
        if test_spec := processor.process(platform, scenario):
            yield test_spec

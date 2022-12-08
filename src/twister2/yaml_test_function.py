"""
Yaml test implementation.

Module creates pytest test function representing Zephyr C tests.

Base on pytest non-python test example:
https://docs.pytest.org/en/6.2.x/example/nonpython.html
"""
from __future__ import annotations

import logging
from typing import Any

import pytest

from twister2.device.device_abstract import DeviceAbstract
from twister2.log_parser.log_parser_abstract import LogParserAbstract
from twister2.yaml_test_specification import YamlTestSpecification

logger = logging.getLogger(__name__)


def yaml_test_function_factory(spec: YamlTestSpecification, parent: Any) -> YamlTestFunction:
    """Generate test function."""
    function = YamlTestFunction.from_parent(
        name=spec.name,
        originalname=spec.original_name,
        parent=parent,
        callobj=YamlTestCase(spec),  # callable object (test function)
    )
    add_markers_from_specification(function, spec)
    return function


def add_markers_from_specification(obj: pytest.Item | pytest.Function, spec: YamlTestSpecification) -> None:
    """
    Add markers to pytest function or item.

    Function adds all required markers base on test specification.

    :param obj: instance of pytest Item or Function
    :param spec: yaml test specification
    """
    obj.add_marker(pytest.mark.platform(spec.platform))
    if spec.type:
        obj.add_marker(pytest.mark.type(spec.type))
    if spec.tags:
        obj.add_marker(pytest.mark.tags(*spec.tags))
    if spec.slow:
        obj.add_marker(pytest.mark.slow)
    if spec.skip:
        obj.add_marker(pytest.mark.skip('Skipped in yaml specification'))


class YamlTestFunction(pytest.Function):
    """Wrapper for pytest.Function to extend functionality."""


class YamlTestCase:
    """Callable class representing yaml test."""

    def __init__(self, spec: YamlTestSpecification, description: str = ''):
        """
        :param spec: test specification
        :param description: test description (docstring)
        """
        self.spec = spec
        self.__doc__ = description

    def __call__(
        self,
        request: pytest.FixtureRequest,
        dut: DeviceAbstract,
        log_parser: LogParserAbstract,
        *args, **kwargs
    ):
        """Method called by pytest when it runs test."""
        if self.spec.build_only or request.config.twister_config.build_only:
            # do not run test for build only
            return

        logger.info('Execution test %s from %s', self.spec.name, self.spec.source_dir)

        log_parser.parse(timeout=self.spec.timeout)

        if log_parser.state == log_parser.STATE.UNKNOWN:
            failed_msg: str = f'Test state is {log_parser.state.value} (timeout has probably occurred)'
        else:
            failed_msg: str = 'Test failed due to: {}'.format('\n'.join(log_parser.messages))
        assert log_parser.state == log_parser.STATE.PASSED, failed_msg

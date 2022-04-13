"""
Yaml test implementation.

Module creates pytest test function representing Zypher C tests.

Base on pytest non-python test example:
https://docs.pytest.org/en/6.2.x/example/nonpython.html
"""
from __future__ import annotations

import logging
from typing import Any

import pytest

from twister2.device.device_abstract import DeviceAbstract
from twister2.log_parser.log_parser_abstract import LogParserAbstract, SubTestStatus
from twister2.twister_config import TwisterConfig
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
    function.add_marker(pytest.mark.platform(spec.platform))
    function.add_marker(pytest.mark.type(spec.type))
    if spec.tags:
        function.add_marker(pytest.mark.tags(*spec.tags))
    if spec.slow:
        function.add_marker(pytest.mark.slow)
    if spec.skip:
        function.add_marker(pytest.mark.skip('Skipped in yaml specification'))
    return function


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
        subtests,
        *args, **kwargs
    ):
        """Method called by pytest when it runs test."""
        if self.spec.build_only or request.config.twister_config.build_only:
            # do not run test for build only
            return

        logger.info('Execution test %s from %s', self.spec.name, self.spec.path)

        # using subtests fixture to log single C test
        # https://pypi.org/project/pytest-subtests/
        for test in log_parser.parse(timeout=self.spec.timeout):
            with subtests.test(msg=test.testname):
                if test.result == SubTestStatus.SKIP:
                    pytest.skip('Skipped on runtime')
                    continue
                assert test.result == SubTestStatus.PASS, f'Subtest {test.testname} failed'

        assert log_parser.state == 'PASSED', 'Test failed due to: {}'.format('\n'.join(log_parser.messages))

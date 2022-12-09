from __future__ import annotations

import logging
from typing import Generator

import pytest
from pytest_subtests import SubTests

from twister2.device.device_abstract import DeviceAbstract
from twister2.exceptions import TwisterConfigurationException
from twister2.log_parser.factory import LogParserFactory
from twister2.log_parser.log_parser_abstract import LogParserAbstract

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def log_parser(
        request: pytest.FixtureRequest, dut: DeviceAbstract, subtests: SubTests
) -> Generator[LogParserAbstract, None, None]:
    """Return log parser."""
    spec = request.session.specifications.get(request.node.nodeid)  # type: ignore
    if not spec:
        msg = f'Could not find test specification for test {request.node.nodeid}'
        logger.error(msg)
        raise TwisterConfigurationException(msg)

    parser_name = spec.harness or 'ztest'  # make ztest default parser
    harness_config = spec.harness_config
    ignore_faults = spec.ignore_faults

    parser_class = LogParserFactory.get_parser(parser_name)
    yield parser_class(stream=dut.iter_stdout,
                       harness_config=harness_config,
                       ignore_faults=ignore_faults,
                       subtests_fixture=subtests)

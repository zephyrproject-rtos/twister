from __future__ import annotations

import logging

import pytest
from pytest_subtests import SubTests

from twister2.device.device_abstract import DeviceAbstract
from twister2.fixtures.common import SetupTestManager
from twister2.log_parser.factory import LogParserFactory
from twister2.log_parser.log_parser_abstract import LogParserAbstract

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def log_parser(
        dut: DeviceAbstract, subtests: SubTests, setup_manager: SetupTestManager
) -> LogParserAbstract | None:
    """Return log parser."""
    spec = setup_manager.specification

    parser_name = spec.harness or 'ztest'  # make ztest default parser
    harness_config = spec.harness_config
    ignore_faults = spec.ignore_faults

    # check if test should be executed, if not than do not create log parser as it won't be used
    if setup_manager.is_executable:
        parser_class = LogParserFactory.get_parser(parser_name)
        return parser_class(stream=dut.iter_stdout,
                            harness_config=harness_config,
                            ignore_faults=ignore_faults,
                            subtests_fixture=subtests)
    else:
        return None

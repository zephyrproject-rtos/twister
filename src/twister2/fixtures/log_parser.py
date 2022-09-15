from __future__ import annotations

import logging

import pytest

from twister2.log_parser.factory import LogParserFactory
from twister2.log_parser.ztest_log_parser import ZtestLogParser

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def log_parser(request: pytest.FixtureRequest, dut) -> ZtestLogParser | None:
    """Return log parser."""
    parser_name = request.function.spec.harness or 'ztest'  # make ztest default parser
    harness_config = request.function.spec.harness_config
    fail_on_fault = False if 'ignore_faults' in request.function.spec.tags else True

    parser_class = LogParserFactory.get_parser(parser_name)
    yield parser_class(dut.out, harness_config=harness_config, fail_on_fault=fail_on_fault)

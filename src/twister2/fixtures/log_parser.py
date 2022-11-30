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
    ignore_faults = request.function.spec.ignore_faults

    parser_class = LogParserFactory.get_parser(parser_name)
    yield parser_class(stream=dut.iter_stdout, harness_config=harness_config, ignore_faults=ignore_faults)

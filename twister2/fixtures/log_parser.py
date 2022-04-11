from __future__ import annotations

import logging

import pytest

from twister2.log_parser.factory import LogParserFactory
from twister2.log_parser.harness_log_parser import HarnessLogParser

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def log_parser(request: pytest.FixtureRequest, dut) -> HarnessLogParser | None:
    """Return log parser."""
    parser_name = request.function.spec.harness or 'harness'  # make harness default parser
    harness_config = request.function.spec.harness_config
    fail_on_fault = True if 'ignore_faults' in request.function.spec.tags else False

    parser_class = LogParserFactory.get_parser(parser_name)
    yield parser_class(dut.out, harness_config=harness_config, fail_on_fault=fail_on_fault)

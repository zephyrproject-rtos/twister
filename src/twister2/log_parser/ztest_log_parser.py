"""
Ztest log parser.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Iterator, Generator

from twister2.exceptions import TwisterFatalError
from twister2.log_parser.log_parser_abstract import SubTestResult, LogParserAbstract

PROJECT_EXECUTION_SUCCESSFUL: str = 'PROJECT EXECUTION SUCCESSFUL'
PROJECT_EXECUTION_FAILED: str = 'PROJECT EXECUTION FAILED'
ZEPHYR_FATAL_ERROR: str = 'ZEPHYR FATAL ERROR'

result_re_pattern: re.Pattern = re.compile(
    r'^.*(?P<result>PASS|FAIL|SKIP|BLOCK) - (test_)?(?P<testname>.*) in (?P<duration>[\d\.]+) seconds$'
)
testsuite_name_re_pattern: re.Pattern = re.compile(r'^.*Running TESTSUITE\s(?P<testsuite>.*)$')

logger = logging.getLogger(__name__)


class ZtestLogParser(LogParserAbstract):
    """Parse Ztest output from log stream."""

    def __init__(self, stream: Iterator[str], *, fail_on_fault: bool = False, **kwargs):
        super().__init__(stream, **kwargs)
        self.detected_suite_names: list[str] = []
        self.fail_on_fault = fail_on_fault

    def parse(self, timeout: float = 60) -> Generator[SubTestResult, None, None]:
        """Parse logs and return list of tests with statuses."""
        end_time = time.time() + timeout
        while self.stream:
            if time.time() > end_time:
                self.messages.append('Timeout')
                break

            try:
                line = next(self.stream)
            except StopIteration:
                return

            if not line:
                continue

            logger.debug(line.rstrip())
            if PROJECT_EXECUTION_FAILED in line:
                logger.error('PROJECT EXECUTION FAILED')
                self.state = self.STATE.FAILED
                self.messages.append('Project execution failed')
                return  # exit: tests finished

            if PROJECT_EXECUTION_SUCCESSFUL in line:
                self.state = self.STATE.FAILED if self.state == self.STATE.FAILED else self.STATE.PASSED
                logger.info('PROJECT EXECUTION SUCCESSFUL')
                return  # exit: tests finished

            if ZEPHYR_FATAL_ERROR in line and self.fail_on_fault:
                logger.error('ZEPHYR FATAL ERROR')
                self.state = self.STATE.FAILED
                raise TwisterFatalError('Zephyr fatal error')

            if match := testsuite_name_re_pattern.match(line):
                test_suite_name = match.group(1)
                logger.info('Found test suite: %s', test_suite_name)
                self.detected_suite_names.append(test_suite_name)

            if match := result_re_pattern.match(line):
                test = SubTestResult(**match.groupdict())
                logger.info('Ztest: %s - %s in %s', test.testname, test.result, test.duration)
                yield test

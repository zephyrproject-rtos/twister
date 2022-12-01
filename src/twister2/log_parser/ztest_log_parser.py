"""
Ztest log parser.
"""
from __future__ import annotations

import enum
import logging
import re
import time
from dataclasses import dataclass
from typing import Iterator

import pytest
from pytest_subtests import SubTests

from twister2.exceptions import TwisterFatalError
from twister2.log_parser.log_parser_abstract import LogParserAbstract

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

    def __init__(self,
                 stream: Iterator[str],
                 *,
                 ignore_faults: bool = False,
                 subtests_fixture: SubTests | None = None,
                 **kwargs):
        super().__init__(stream, **kwargs)
        self.subtests_fixture: SubTests = subtests_fixture
        self.ignore_faults: bool = ignore_faults
        self.detected_suite_names: list[str] = []
        self.subtest_results: list[SubTestResult] = []

    def parse(self, timeout: float = 60) -> None:
        """Parse logs and create list of subtests with statuses."""
        end_time = time.time() + timeout
        while self.stream:
            if time.time() > end_time:
                self.messages.append('Timeout')
                return

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

            if ZEPHYR_FATAL_ERROR in line and not self.ignore_faults:
                logger.error('ZEPHYR FATAL ERROR')
                self.state = self.STATE.FAILED
                raise TwisterFatalError('Zephyr fatal error')

            if match := testsuite_name_re_pattern.match(line):
                test_suite_name = match.group(1)
                logger.info('Found test suite: %s', test_suite_name)
                self.detected_suite_names.append(test_suite_name)

            if result_match := result_re_pattern.match(line):
                subtest = SubTestResult(**result_match.groupdict())
                self.subtest_results.append(subtest)
                logger.info('Ztest: %s - %s in %s', subtest.testname, subtest.result, subtest.duration)
                self._register_pytest_subtests(subtest)

    def _register_pytest_subtests(self, subtest: SubTestResult):
        '''
        Using subtests fixture to log single C test
        https://pypi.org/project/pytest-subtests/
        '''
        if self.subtests_fixture is None:
            return

        with self.subtests_fixture.test(msg=subtest.testname):
            if subtest.result == SubTestStatus.SKIP:
                pytest.skip('Skipped on runtime')
            if subtest.result == SubTestStatus.BLOCK:
                pytest.skip('Blocked')
            assert subtest.result == SubTestStatus.PASS, f'Subtest {subtest.testname} failed'


class SubTestStatus(str, enum.Enum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    SKIP = 'SKIP'
    BLOCK = 'BLOCK'  # there is no `block` status in pytest, should be handled as skip

    def __str__(self):
        return self.name


@dataclass
class SubTestResult:
    """Store result for single C tests."""
    testname: str
    result: SubTestStatus
    duration: float

    def __post_init__(self):
        if isinstance(self.duration, str):
            self.duration = float(self.duration)
        if isinstance(self.result, str):
            self.result = SubTestStatus(self.result)

    def asdict(self) -> dict:
        """Return JSON serialized dictionary."""
        return dict(
            testname=self.testname,
            result=str(self.result),
            duration=self.duration
        )

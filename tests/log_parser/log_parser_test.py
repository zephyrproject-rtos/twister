from pathlib import Path

import pytest
from twister2.exceptions import TwisterFatalError
from twister2.log_parser import SubTestStatus
from twister2.log_parser.ztest_log_parser import ZtestLogParser


def test_if_ztest_log_parser_returns_correct_status(resources: Path):
    with open(resources / 'device_log.txt', encoding='UTF-8') as file:
        parser = ZtestLogParser(stream=file, fail_on_fault=False)
        sub_tests = list(parser.parse())
        assert len(sub_tests) == 45
        assert parser.state == 'PASSED'
        assert parser.detected_suite_names == ['common']
        assert len([tc for tc in sub_tests if tc.result == SubTestStatus.SKIP]) == 3
        assert len([tc for tc in sub_tests if tc.result == SubTestStatus.FAIL]) == 0


def test_if_ztest_log_parser_fails_on_fault(resources: Path):
    with open(resources / 'device_log_with_fail.txt', 'r', encoding='UTF-8') as file:
        parser = ZtestLogParser(stream=file, fail_on_fault=True)
        with pytest.raises(TwisterFatalError, match='Zephyr fatal error'):
            list(parser.parse())


def test_if_harness_log_parser_not_fails_on_fault(resources: Path):
    with open(resources / 'device_log_with_fail_dynamic_thread.txt', 'r', encoding='UTF-8') as file:
        stream = (line for line in file)
        parser = ZtestLogParser(stream=stream, fail_on_fault=False)
        sub_tests = list(parser.parse())
        assert len(sub_tests) == 4
        assert parser.state == 'PASSED'
        assert parser.detected_suite_names == ['thread_dynamic']
        assert len([tc for tc in sub_tests if tc.result == SubTestStatus.PASS]) == 4

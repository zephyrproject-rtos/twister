from pathlib import Path

import pytest

from twister2.exceptions import TwisterFatalError
from twister2.log_parser.harness_log_parser import HarnessLogParser
from twister2.log_parser import SubTestStatus

DATA_DIR: Path = Path(__file__).parent / 'data'


def test_harness_log_parser():
    with open(DATA_DIR / 'device_log.txt', 'r', encoding='UTF-8') as file:
        parser = HarnessLogParser(stream=file, fail_on_fault=False)
        sub_tests = list(parser.parse())
        assert len(sub_tests) == 45
        assert parser.state == 'PASSED'
        assert parser.detected_suite_names == ['common']
        assert len([tc for tc in sub_tests if tc.result == SubTestStatus.SKIP]) == 3
        assert len([tc for tc in sub_tests if tc.result == SubTestStatus.FAIL]) == 0


def test_if_harness_log_parser_fails_on_fault():
    with open(DATA_DIR / 'device_log_with_fail.txt', 'r', encoding='UTF-8') as file:
        parser = HarnessLogParser(stream=file, fail_on_fault=True)
        with pytest.raises(TwisterFatalError):
            list(parser.parse())


def test_if_harness_log_parser_not_fails_on_fault():
    with open(DATA_DIR / 'device_log_with_fail.txt', 'r', encoding='UTF-8') as file:
        stream = (line for line in file)
        parser = HarnessLogParser(stream=stream, fail_on_fault=False)
        sub_tests = list(parser.parse())
        assert len(sub_tests) == 41
        assert parser.state == 'FAILED'
        assert parser.detected_suite_names == ['common']
        assert len([tc for tc in sub_tests if tc.result == SubTestStatus.SKIP]) == 2
        assert len([tc for tc in sub_tests if tc.result == SubTestStatus.FAIL]) == 1

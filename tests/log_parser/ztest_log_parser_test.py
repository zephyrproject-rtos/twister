from pathlib import Path

import pytest

from twister2.exceptions import TwisterFatalError
from twister2.log_parser.ztest_log_parser import SubTestStatus, ZtestLogParser


def test_if_ztest_log_parser_returns_correct_status(resources: Path):
    with open(resources / 'ztest_log.txt', encoding='UTF-8') as file:
        parser = ZtestLogParser(stream=file, ignore_faults=False)
        parser.parse()
        assert len(parser.subtest_results) == 45
        assert parser.state == parser.STATE.PASSED
        assert parser.detected_suite_names == ['common']
        assert len([st for st in parser.subtest_results if st.result == SubTestStatus.SKIP]) == 3
        assert len([st for st in parser.subtest_results if st.result == SubTestStatus.FAIL]) == 0


def test_if_ztest_log_parser_returns_correct_status_with_no_subtests():
    log = """
        ***** delaying boot 500ms (per build configuration) *****
        *** Booting Zephyr OS build zephyr-v3.0.0-2155-g4e9d9f2ef7a1  (delayed boot 500ms) ***
        Running TESTSUITE common
        PROJECT EXECUTION SUCCESSFUL
    """.split('\n')
    parser = ZtestLogParser(stream=iter(log), ignore_faults=False)
    parser.parse()
    assert len(parser.subtest_results) == 0
    assert parser.state == parser.STATE.PASSED


def test_if_ztest_log_parser_returns_correct_status_for_all_tests_skipped():
    log = """
        ***** delaying boot 500ms (per build configuration) *****
        *** Booting Zephyr OS build zephyr-v3.0.0-2155-g4e9d9f2ef7a1  (delayed boot 500ms) ***
        Running TESTSUITE common
        ===================================================================
        START - test_nop
        time k_cycle_get_32() takes 0 cycles
         SKIP - test_nop in 0.0 seconds
        PROJECT EXECUTION SUCCESSFUL
    """.split('\n')
    parser = ZtestLogParser(stream=iter(log), ignore_faults=False)
    parser.parse()
    assert len(parser.subtest_results) == 1
    assert parser.state == parser.STATE.PASSED
    assert len([st for st in parser.subtest_results if st.result == SubTestStatus.SKIP]) == 1


def test_if_ztest_log_parser_returns_correct_status_when_subtest_failed():
    log = """
        ***** delaying boot 500ms (per build configuration) *****
        *** Booting Zephyr OS build zephyr-v3.0.0-2155-g4e9d9f2ef7a1  (delayed boot 500ms) ***
        START - test_clock_cycle_64
        FAIL - test_clock_cycle_64 in 0.20 seconds
        PROJECT EXECUTION FAILED
    """.split('\n')
    parser = ZtestLogParser(stream=iter(log), ignore_faults=False)
    parser.parse()
    assert parser.state == parser.STATE.FAILED
    assert len(parser.subtest_results) == 1
    assert len([st for st in parser.subtest_results if st.result == SubTestStatus.FAIL]) == 1


def test_if_ztest_log_parser_returns_correct_status_with_no_input():
    log = []
    parser = ZtestLogParser(stream=iter(log), ignore_faults=False)
    parser.parse()
    assert len(parser.subtest_results) == 0
    assert parser.state == parser.STATE.UNKNOWN


def test_if_ztest_log_parser_fails_on_fault(resources: Path):
    with open(resources / 'ztest_log_with_fail.txt', 'r', encoding='UTF-8') as file:
        parser = ZtestLogParser(stream=file, ignore_faults=False)
        with pytest.raises(TwisterFatalError, match='Zephyr fatal error'):
            list(parser.parse())


def test_if_ztest_log_parser_not_fails_on_fault(resources: Path):
    with open(resources / 'ztest_log_with_fail_dynamic_thread.txt', 'r', encoding='UTF-8') as file:
        stream = (line for line in file)
        parser = ZtestLogParser(stream=stream, ignore_faults=True)
        parser.parse()
        assert len(parser.subtest_results) == 4
        assert parser.state == parser.STATE.PASSED
        assert parser.detected_suite_names == ['thread_dynamic']
        assert len([st for st in parser.subtest_results if st.result == SubTestStatus.PASS]) == 4


# TODO: Write test for BLOCK status for subtest

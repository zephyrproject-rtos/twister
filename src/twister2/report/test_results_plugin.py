"""
Plugin to generate custom report for twister.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Sequence

import pytest
from pytest_subtests import SubTestReport

from twister2.environment.environment import get_toolchain_version, get_zephyr_repo_info
from twister2.report.base_report_writer import BaseReportWriter
from twister2.report.helper import (
    get_item_arch,
    get_item_build_only_status,
    get_item_platform,
    get_item_runnable_status,
    get_item_type,
    get_retries,
    get_run_id,
    get_suite_name,
    get_test_name,
)
from twister2.report.test_results_json import JsonResultsReport

logger = logging.getLogger(__name__)

TIME_DECIMAL_PLACES = 2
TIME_DECIMAL_PLACES_SUBTEST = 2


class Status:
    PASSED = 'passed'
    XPASSED = 'xpassed'
    FAILED = 'failed'
    XFAILED = 'xfailed'
    ERROR = 'error'
    SKIPPED = 'skipped'
    RERUN = 'rerun'


class TestResult:
    """Class stores test result for single test."""

    def __init__(self, nodeid: str):
        self.test_id: str = nodeid.encode('utf-8').decode('unicode_escape')
        self.nodeid = nodeid
        self.name: str = self.test_id
        self.status: str | None = None
        self.item: str = nodeid
        self.report = None
        self.config = None
        self.duration: float = 0.0  #: whole time spent on running test
        self.call_duration: float = 0.0  #: time spent only on execution (without setup and teardown)
        self.message: str = ''
        self.subtests: list = []

    def __repr__(self):
        return f'{self.__class__.__name__}({self.status!r})'

    def extract_results(self, outcome: str, report: pytest.TestReport, config: pytest.Config):
        if getattr(report, 'when', 'call') != 'call':
            self.test_id = '::'.join([report.nodeid, report.when])  # type: ignore[list-item]
        self._update_status(outcome)
        self.report = report
        self.config = config
        self.message = report.longreprtext

    def add_subtest(self, subtest: dict) -> None:
        self._update_status(subtest['status'])
        self.subtests.append(subtest)

    def _update_status(self, new_status: str):
        order = (
            Status.SKIPPED,
            Status.PASSED,
            Status.XPASSED,
            Status.XFAILED,
            Status.RERUN,
            Status.FAILED,
            Status.ERROR,
        )
        if self.status is None:
            self.status = new_status
        else:
            status = order[max(order.index(self.status), order.index(new_status))]
            self.status = status


class TestResultsPlugin:
    """Class collects results and crates result report."""

    def __init__(self, config: pytest.Config, writers: Sequence[BaseReportWriter]):
        """
        :param config: pytest configuration
        :param writers: list of report writers
        """
        self.config = config
        self.writers = writers
        self.counter: Counter = Counter(passed=0, failed=0, skipped=0, xfailed=0, xpassed=0, error=0)
        self.test_results: dict[str, TestResult] = {}
        self.items: dict[str, pytest.Item] = {}

    def pytest_report_collectionfinish(self, config: pytest.Config, items: list[pytest.Item]):
        self.items = {item.nodeid: item for item in items}

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection(self, session):
        yield
        if not hasattr(session, 'items'):
            # Collection was skipped (probably due to xdist)
            session.perform_collect()

    def pytest_runtest_logreport(self, report: pytest.TestReport):
        if report.nodeid not in self.test_results:
            self.test_results[report.nodeid] = TestResult(report.nodeid)

        result = self.test_results[report.nodeid]

        if not self._is_sub_test(report):
            result.duration += getattr(report, 'duration', 0.0)
            if getattr(report, 'when', '') == 'call':
                result.call_duration = getattr(report, 'duration', 0.0)

        outcome = self._get_outcome(report)
        if not outcome:
            return

        if self._is_sub_test(report):
            ztest_testcase_duration = self._get_ztest_testcase_duration(report)
            result.add_subtest(
                dict(
                    identifier=report.context.msg,
                    execution_time=f'{ztest_testcase_duration:.{TIME_DECIMAL_PLACES_SUBTEST}f}',
                    status=outcome,
                )
            )
        else:
            result.extract_results(outcome, report, self.config)

    @staticmethod
    def _is_sub_test(report: pytest.TestReport) -> bool:
        return isinstance(report, SubTestReport)

    @staticmethod
    def _get_ztest_testcase_duration(report: pytest.TestReport) -> float:
        duration: float = 0.0
        context = getattr(report, 'context', None)
        if context is None:
            return duration
        kwargs = getattr(context, 'kwargs', None)
        if kwargs is None:
            return duration
        duration = kwargs.get('ztest_testcase_duration', 0.0)
        return duration

    def pytest_sessionstart(self, session: pytest.Session):
        self.session_start_time = time.time()

    def pytest_sessionfinish(self, session: pytest.Session):
        self.session_finish_time = time.time()
        data = self._generate_report(session)
        if self.config.option.only_failed:
            data = self._merge_with_load_tests_data(data, self.config.option.load_tests_path)
        self._save_report(data)

    def pytest_terminal_summary(self, terminalreporter):
        for writer in self.writers:
            writer.print_summary(terminalreporter)

    def _get_outcome(self, report: pytest.TestReport) -> str | None:  # type: ignore[return]
        if report.failed:
            if report.when != 'call':
                return Status.ERROR
            elif hasattr(report, 'wasxfail'):
                return Status.XFAILED
            else:
                return Status.FAILED
        elif report.skipped:
            if hasattr(report, 'wasxfail'):
                return Status.XFAILED
            else:
                return Status.SKIPPED
        elif report.passed and report.when == 'call':
            if hasattr(report, 'wasxfail'):
                return Status.XPASSED
            else:
                return Status.PASSED

    def _generate_report(self, session: pytest.Session) -> dict:
        """Return test report data as dictionary."""
        tests_list: list = []
        subtests_total = 0
        subtests_pass_count = 0
        subtests_fail_count = 0
        subtests_skip_count = 0

        for result in self.test_results.values():
            result: TestResult  # type: ignore
            item = self.items.get(result.nodeid)

            if not item:
                continue

            self.counter[result.status] += 1
            subtests_total += len(result.subtests)
            subtests_pass_count += sum(1 for st in result.subtests if st['status'] == Status.PASSED)
            subtests_fail_count += sum(1 for st in result.subtests if st['status'] == Status.FAILED)
            subtests_skip_count += sum(1 for st in result.subtests if st['status'] == Status.SKIPPED)

            testsuites = dict(
                name=get_suite_name(item),
                arch=get_item_arch(item),
                platform=get_item_platform(item),
                run_id=get_run_id(item),
                runnable=get_item_runnable_status(item),
                retries=get_retries(item),
                status=result.status,
                message=result.message,
                execution_time=f'{result.call_duration:.{TIME_DECIMAL_PLACES}f}',
                duration=f'{result.duration:.{TIME_DECIMAL_PLACES}f}',
                test_name=get_test_name(item),
                nodeid=item.nodeid,
                type=get_item_type(item),
                build_only=get_item_build_only_status(item),
                testcases=result.subtests,
            )
            tests_list.append(testsuites)

        summary = dict(self.counter)
        summary['total'] = sum(self.counter.values())
        summary['subtests_total'] = subtests_total
        summary['subtests_passed'] = subtests_pass_count
        summary['subtests_failed'] = subtests_fail_count
        summary['subtests_skipped'] = subtests_skip_count

        return dict(
            environment=self._get_environment(),
            configuration=self.config.twister_config.asdict(),  # type: ignore
            summary=summary,
            testsuites=tests_list,
        )

    def _merge_with_load_tests_data(self, data: dict, load_tests_path: str) -> dict:
        with open(load_tests_path, 'r') as fp:
            load_data = json.load(fp)
        test_list: list = []
        for ts in load_data['testsuites']:
            if (matched_ts := self._find_testsuite(data['testsuites'], ts['name'])):
                test_list.append(matched_ts)
            else:
                test_list.append(ts)
        data['testsuites'] = test_list
        return data

    def _find_testsuite(self, testsuites: list[dict], name: str) -> dict | None:
        for ts in testsuites:
            if ts['name'] == name:
                return ts
        return None

    def _get_environment(self) -> dict:
        duration = self.session_finish_time - self.session_start_time
        repo_info = get_zephyr_repo_info(self.config.twister_config.zephyr_base)
        toolchain = get_toolchain_version(self.config.twister_config.output_dir, self.config.twister_config.zephyr_base)

        environment = dict(
            os=os.name,
            zephyr_version=repo_info.zephyr_version,  # type: ignore[attr-defined]
            commit_date=repo_info.commit_date,  # type: ignore[attr-defined]
            toolchain=toolchain,
            run_date=datetime.now(timezone.utc).isoformat(timespec='seconds'),
            pc_name=platform.node() or 'N/A',
            duration=f'{duration:.{TIME_DECIMAL_PLACES}f}',
        )
        return environment

    def _save_report(self, data: dict) -> None:
        for writer in self.writers:
            writer.write(data)


def pytest_addoption(parser: pytest.Parser):
    custom_reports = parser.getgroup('Twister reports')
    custom_reports.addoption(
        '--results-json',
        dest='results_json_path',
        metavar='PATH',
        action='store',
        default=None,
        help='generate test results report in JSON format'
    )


def pytest_configure(config: pytest.Config):
    if hasattr(config, 'workerinput'):  # xdist worker
        return

    if not (config.getoption('twister') or config.getini('twister')):
        return

    test_results_writers = []
    test_result_json_path = None
    if config.getoption('results_json_path'):
        test_result_json_path = config.getoption('results_json_path')
    else:
        test_result_json_path = os.path.join(config.getoption('output_dir'), 'twister.json')
    test_results_writers.append(JsonResultsReport(test_result_json_path))

    if test_results_writers and not config.option.collectonly and not config.option.save_tests_path:
        config.pluginmanager.register(
            plugin=TestResultsPlugin(config, writers=test_results_writers),
            name='test_results'
        )

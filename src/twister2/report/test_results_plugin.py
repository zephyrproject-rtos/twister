"""
Plugin to generate custom report for twister.
"""
from __future__ import annotations

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
    get_item_build_only_status,
    get_item_platform,
    get_item_platform_allow,
    get_item_quarantine,
    get_item_runnable_status,
    get_item_tags,
    get_item_type,
    get_suite_name,
    get_test_name,
)
from twister2.report.test_results_json import JsonResultsReport


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

    def __init__(self, outcome: str, report: pytest.TestReport, config: pytest.Config):
        self.test_id: str = report.nodeid.encode('utf-8').decode('unicode_escape')
        self.nodeid = report.nodeid
        self.name: str = self.test_id
        if getattr(report, 'when', 'call') != 'call':
            self.test_id = '::'.join([report.nodeid, report.when])  # type: ignore[list-item]
        self.status = outcome
        self.item = report.nodeid
        self.report = report
        self.config = config
        self.duration: float = getattr(report, 'duration', 0.0)  #: whole time spent on running test
        self.call_duration: float = 0.0  #: time spent only on execution (without setup and teardown)
        self.message: str = report.longreprtext
        self.subtests: list = []

    def __repr__(self):
        return f'{self.__class__.__name__}({self.status!r})'

    def add_subtest(self, subtest: dict) -> None:
        order = (
            Status.SKIPPED,
            Status.PASSED,
            Status.XPASSED,
            Status.XFAILED,
            Status.RERUN,
            Status.FAILED,
            Status.ERROR,
        )
        status = order[max(order.index(self.status), order.index(subtest['status']))]
        self.status = status
        self.subtests.append(subtest)


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

    def pytest_runtest_call(self, item):
        time_start = time.time()
        yield
        duration = time.time() - time_start
        self.test_results[item.nodeid].call_duration = duration

    def pytest_runtest_logreport(self, report: pytest.TestReport):
        outcome = self._get_outcome(report)
        if not outcome:
            return

        if report.nodeid not in self.test_results:
            self.test_results[report.nodeid] = TestResult(outcome, report, self.config)
        if self._is_sub_test(report):
            self.test_results[report.nodeid].add_subtest(
                dict(
                    name=report.context.msg,
                    status=outcome,
                    duration=round(report.duration, 2),
                )
            )

    @staticmethod
    def _is_sub_test(report: pytest.TestReport) -> bool:
        return isinstance(report, SubTestReport)

    def pytest_sessionstart(self, session: pytest.Session):
        self.session_start_time = time.time()

    def pytest_sessionfinish(self, session: pytest.Session):
        self.session_finish_time = time.time()
        data = self._generate_report(session)
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

            test = dict(
                suite_name=get_suite_name(item),
                test_name=get_test_name(item),
                nodeid=item.nodeid,
                platform=get_item_platform(item),
                tags=get_item_tags(item),
                type=get_item_type(item),
                build_only=get_item_build_only_status(item),
                runnable=get_item_runnable_status(item),
                platform_allow=get_item_platform_allow(item),
                status=result.status,
                message=result.message,
                quarantine=get_item_quarantine(item),
                duration=round(result.duration, 2),
                execution_time=round(result.call_duration, 2),
                subtests=result.subtests,
            )
            tests_list.append(test)

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
            tests=tests_list,
        )

    def _get_environment(self) -> dict:
        duration = self.session_finish_time - self.session_start_time
        repo_info = get_zephyr_repo_info()
        toolchain = get_toolchain_version(self.config.twister_config.output_dir, self.config.twister_config.zephyr_base)

        environment = dict(
            os=os.name,
            zephyr_version=repo_info.zephyr_version,  # type: ignore[attr-defined]
            commit_date=repo_info.commit_date,  # type: ignore[attr-defined]
            toolchain=toolchain,
            run_date=datetime.now(timezone.utc).isoformat(timespec='seconds'),
            pc_name=platform.node() or 'N/A',
            duration=round(duration, 2),
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

    test_results_writers = []
    if test_result_json_path := config.getoption('results_json_path'):
        test_results_writers.append(JsonResultsReport(test_result_json_path))

    if test_results_writers and not config.option.collectonly:
        config.pluginmanager.register(
            plugin=TestResultsPlugin(config, writers=test_results_writers),
            name='test_results'
        )

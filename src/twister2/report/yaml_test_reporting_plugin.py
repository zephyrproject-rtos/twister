
""" This plugin modifies the default console output for yaml
tests and subtests (testcases) when verbosity >=2."""

from __future__ import annotations

import pytest
from pytest_subtests import SubTestReport


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(report, config):

    if not hasattr(config, 'twister_config'):
        return

    if hasattr(report, 'wasxfail'):
        return None

    # Do nothing extra if the hook was called for other than yaml/subtest reporting.
    if report.when != 'call' or '.yaml' not in report.fspath and not isinstance(report, SubTestReport):
        return None

    # report.location[0] is used when verbosity >=2. By default plugin is printing noise for (yaml/sub)tests
    if not isinstance(report, SubTestReport):
        # this change the useless path to "configuration" to differentiate from "ztestcase" printed by subtests
        # the rest is not changed and pytest_report_teststatus from pytest is further processing the report
        loc = list(report.location)
        loc[0] = 'configuration'
        report.location = tuple(loc)
        return None

    else:
        # this change the useless path to (sub)testcase name
        loc = list(report.location)
        loc[0] = f'ztestcase "{report.context.msg}"'
        report.location = tuple(loc)

        output_formating = {
            'passed': ['subtests passed', ',', 'SUBPASS'],
            'skipped': ['subtests skipped', '-', 'SUBSKIP'],
            'failed': ['subtests failed', 'f', 'SUBFAIL'],
        }
        # We only want to see subtests' status in the console if verbosity > 1."""
        # This removes the substatuses from console outputs if verbosity <= 1
        if config.option.verbose <= 1:
            for key in output_formating.keys():
                output_formating[key][1] = ''
                output_formating[key][2] = ''

        # No further hooks to this plugin (in particular the original pytest pytest_report_teststatus)
        # are executed after firts non-None return)
        return tuple(output_formating[report.outcome])

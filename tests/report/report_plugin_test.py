import json
import textwrap
from pathlib import Path

import pytest


def test_if_pytest_generate_testplan_json(pytester, copy_example) -> None:
    output_testplan: Path = pytester.path / 'testplan.json'
    result = pytester.runpytest(
        str(copy_example),
        f'--zephyr-base={str(copy_example)}',
        '--platform=qemu_cortex_m3',
        f'--testplan-json={output_testplan}',
        '--collect-only'
    )
    assert output_testplan.is_file()
    result.stdout.fnmatch_lines_random([
        '*generated*results*report*file:*testplan.json*'
    ])


@pytest.mark.parametrize('extra_args', ['-n 0', '-n 2'], ids=['no_xdist', 'xdist'])
def test_if_pytest_generate_testplan_csv(pytester, copy_example, extra_args) -> None:
    output_testplan: Path = pytester.path / 'testplan.csv'
    result = pytester.runpytest(
        str(copy_example),
        f'--zephyr-base={str(copy_example)}',
        '--platform=qemu_cortex_m3',
        f'--testplan-csv={output_testplan}',
        '--collect-only',
        extra_args
    )
    assert output_testplan.is_file()
    result.stdout.fnmatch_lines_random([
        '*generated*results*report*file:*testplan.csv*'
    ])


@pytest.mark.parametrize('extra_args', ['-n 0', '-n 2'], ids=['no_xdist', 'xdist'])
def test_if_pytest_generates_json_results_with_expected_data(pytester, extra_args) -> None:
    test_file_content = textwrap.dedent("""\
        import pytest

        @pytest.fixture
        def make_error():
            assert 0

        def test_pass():
            pass

        def test_fail():
            assert 0

        @pytest.mark.xfail(reason='expected fail')
        def test_xpass():
            assert 1

        @pytest.mark.xfail(reason='expected fail')
        def test_xfail():
            assert 0

        @pytest.mark.skip
        def test_skip():
            pass

        def test_error(make_error):
            pass

    """)
    test_file = pytester.path / 'foobar_test.py'
    test_file.write_text(test_file_content)
    output_result: Path = pytester.path / 'twister.json'

    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        f'--results-json={output_result}',
        extra_args
    )

    result.assert_outcomes(passed=1, failed=1, errors=1, xfailed=1, xpassed=1, skipped=1)
    assert output_result.is_file()
    with output_result.open() as file:
        report_data = json.load(file)
    assert set(report_data.keys()) == {'testsuites', 'environment', 'configuration', 'summary'}
    assert len(report_data['testsuites']) == 6
    assert set(report_data['testsuites'][0].keys()) == {
        'name',
        'test_name',
        'nodeid',
        'platform',
        'arch',
        'type',
        'build_only',
        'runnable',
        'run_id',
        'status',
        'duration',
        'execution_time',
        'message',
        'testcases',
    }
    assert report_data['summary'] == {
        'passed': 1,
        'failed': 1,
        'skipped': 1,
        'xfailed': 1,
        'xpassed': 1,
        'error': 1,
        'total': 6,
        'subtests_failed': 0,
        'subtests_passed': 0,
        'subtests_skipped': 0,
        'subtests_total': 0
    }
    assert set(report_data['environment'].keys()) == {
        'os',
        'zephyr_version',
        'commit_date',
        'run_date',
        'toolchain',
        'pc_name',
        'duration'
    }

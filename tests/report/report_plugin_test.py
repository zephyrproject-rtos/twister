import json
import textwrap
from pathlib import Path

import pytest


def test_if_pytest_generate_testplan_json(pytester, copy_example) -> None:
    output_testplan: Path = pytester.path / 'tesplan.json'
    result = pytester.runpytest(
        str(copy_example),
        f'--zephyr-base={str(copy_example)}',
        '--platform=qemu_cortex_m3',
        f'--testplan-json={output_testplan}',
        '--collect-only'
    )
    assert output_testplan.is_file()
    result.stdout.fnmatch_lines_random([
        '*generated*results*report*file:*tesplan.json*'
    ])


@pytest.mark.parametrize('extra_args', ['-n 0', '-n 2'], ids=['no_xdist', 'xdist'])
def test_if_pytest_generate_testplan_csv(pytester, copy_example, extra_args) -> None:
    output_testplan: Path = pytester.path / 'tesplan.csv'
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
        '*generated*results*report*file:*tesplan.csv*'
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

        def test_subtests(subtests):
            for i in range(5):
                with subtests.test(msg="custom message", i=i):
                    assert i % 2 == 0
    """)
    test_file = pytester.path / 'foobar_test.py'
    test_file.write_text(test_file_content)
    output_result: Path = pytester.path / 'result.json'

    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        f'--results-json={output_result}',
        extra_args
    )

    result.assert_outcomes(passed=2, failed=3, errors=1, xfailed=1, xpassed=1, skipped=1)
    assert output_result.is_file()
    with output_result.open() as file:
        report_data = json.load(file)
    assert set(report_data.keys()) == {'tests', 'environment', 'configuration', 'summary'}
    assert len(report_data['tests']) == 7
    assert set(report_data['tests'][0].keys()) == {
        'suite_name',
        'test_name',
        'nodeid',
        'platform',
        'tags',
        'type',
        'build_only',
        'runnable',
        'platform_allow',
        'status',
        'quarantine',
        'duration',
        'execution_time',
        'message',
        'subtests',
    }
    assert report_data['summary'] == {
        'passed': 1,
        'failed': 2,
        'skipped': 1,
        'xfailed': 1,
        'xpassed': 1,
        'error': 1,
        'total': 7,
        'subtests_total': 5,
        'subtests_passed': 3,
        'subtests_failed': 2,
        'subtests_skipped': 0
    }

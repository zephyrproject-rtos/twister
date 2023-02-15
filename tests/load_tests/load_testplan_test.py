
import json
import os
import re
import shutil
from pathlib import Path
from unittest import mock

import pytest


# use `autouse` to run tests in sequence (without it, only first test i passed)
@pytest.fixture(autouse=True)
def patched_yaml_call():
    with mock.patch('twister2.yaml_test_function.YamlTestCase.__call__', return_value=None) as call:
        yield call


@pytest.mark.parametrize('extra_args', ['-n 0', '-n 2'], ids=['no_xdist', 'xdist'])
def test_if_tesplan_is_saved(pytester, copy_example, extra_args):
    saveplan: Path = pytester.path / 'saveplan.json'
    result = pytester.runpytest(
        str(copy_example),
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--save-tests={saveplan}',
        extra_args
    )

    assert saveplan.is_file()
    result.stdout.fnmatch_lines_random([
        '*generated*results*report*file:*saveplan.json*'
    ])


def test_if_tesplan_is_loaded_from_v1_plan(pytester, copy_example, resources):
    savedplan: Path = resources / 'testplan_v1.json'
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        f'--load-tests={savedplan}',
        '--co'
    )

    result.stdout.re_match_lines_random([
        r'.*sample.basic.helloworld[native_posix]*',
        r'.*xyz.common_merge_1\[native_posix\]*'
    ])


def test_if_tesplan_is_run(pytester, copy_example, resources):
    savedplan: Path = resources / 'testplan_v1.json'
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        f'--load-tests={savedplan}'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=2, failed=0, errors=0, skipped=0)
    result.stdout.fnmatch_lines([
        '*tests/hello_world*',
        '*tests/common*',
    ])


def test_if_loaded_only_failed_with_given_load_tests(pytester, copy_example, resources):
    savedplan: Path = resources / 'twister_v1.json'

    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        f'--load-tests={savedplan}',
        '--only-failed'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=1, failed=0, errors=0, skipped=0)
    result.stdout.fnmatch_lines(['*tests/common*'])
    result.stdout.no_fnmatch_line('*tests/hello_world*')
    with open(Path('twister-out') / 'twister.json') as fp:
        json_report = json.load(fp)
    assert json_report['testsuites'][1]['retries'] == 3


def test_if_loaded_only_failed_from_default_dir(pytester, copy_example, resources):
    outdir: Path = pytester.path / 'twister-out'
    os.makedirs(outdir, exist_ok=True)
    shutil.copy(resources / 'twister_v1.json', outdir / 'twister.json')
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--only-failed',
        f'--outdir={str(outdir)}'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=1, failed=0, errors=0, skipped=0)
    result.stdout.fnmatch_lines(['*tests/common*'])
    result.stdout.no_fnmatch_line('*tests/hello_world*')


def test_if_tesplan_is_saved_and_loaded(pytester, copy_example):
    saveplan: Path = pytester.path / 'saveplan.json'
    result = pytester.runpytest(
        str(copy_example),
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--save-tests={saveplan}'
    )
    num_of_collected_tests = 0
    num_of_collected_tests = int(re.search(r'collected\s+(\d+)\s+items', str(result.stdout)).group(1))
    assert num_of_collected_tests
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        f'--load-tests={saveplan}'
    )
    result.assert_outcomes(passed=num_of_collected_tests)


from pathlib import Path


def test_twister_help(pytester):
    result = pytester.runpytest('--help')
    result.stdout.fnmatch_lines_random([
        '*Twister reports:*',
        '*--testplan-csv=PATH*generate test plan in CSV format*',
        '*--testplan-json=PATH*generate test plan in JSON format*',
        '*--results-json=PATH*generate test results report in JSON format*',
        '*Twister:*',
        '*--build-only*build only*',
        '*--platform=PLATFORM*build tests for specific platforms*',
        '*--board-root=PATH*directory to search for board configuration files*',
        '*--zephyr-base=PAT*base directory for Zephyr*',
        '*--quarantine-list=*',
        '*--clear={no,delete,archive}*',
        '*Clear twister artifacts*',
    ])


def test_if_pytest_discovers_twister_tests_with_default_platform(pytester, resources) -> None:
    pytester.copy_example(str(resources))
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--co',
    )
    result.stdout.re_match_lines_random([
        r'.*sample.basic.helloworld\[native_posix\].*',
    ])


def test_if_pytest_discovers_twister_tests_with_provided_platform(pytester, resources) -> None:
    pytester.copy_example(str(resources))
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=qemu_cortex_m3',
        '--co',
    )
    result.stdout.re_match_lines_random([
        r'.*bluetooth.mesh.mesh_shell\[qemu_cortex_m3\].*',
    ])


def test_if_pytest_generate_testplan_json(pytester, resources) -> None:
    pytester.copy_example(str(resources))
    output_testplan: Path = pytester.path / 'tesplan.json'
    pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=qemu_cortex_m3',
        f'--testplan-json={output_testplan}',
        '--co'
    )
    assert output_testplan.is_file()


def test_if_pytest_generate_testplan_csv(pytester, resources) -> None:
    pytester.copy_example(str(resources))
    output_testplan: Path = pytester.path / 'tesplan.csv'
    pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=qemu_cortex_m3',
        f'--testplan-csv={output_testplan}',
        '--co'
    )
    assert output_testplan.is_file()

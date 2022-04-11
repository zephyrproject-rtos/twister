from pathlib import Path

import pytest

TEST_DIR = Path(__file__).parent


@pytest.fixture()
def yaml_test(testdir):
    testdir.copy_example(TEST_DIR / 'data/testcase.yaml')
    testdir.copy_example(TEST_DIR / 'data/device.log')
    testdir.makeconftest('pytest_plugins = ["twister2.plugin"]')
    return testdir


def test_twister_help(yaml_test):
    result = yaml_test.runpytest('--help')
    print(result.stdout)
    result.stdout.fnmatch_lines_random([
        '*Twister reports:*',
        '*--testplan-csv=PATH*generate test plan in CSV format*',
        '*--testplan-json=PATH*generate test plan in JSON format*',
        '*--results-json=PATH*generate test results report in JSON format*',
        '*Twister:*',
        '*--build-only*build only*',
        '*--platform=PLATFORM*build tests for specific platforms*',
        '*--board-root=PATH*directory to search for board configuration files*',
        '*--zephyr-base=path*base directory for Zephyr*',
    ])


@pytest.mark.skip('WIP')
def test_twister(yaml_test):
    testplan_file = TEST_DIR / 'twister.csv'
    result = yaml_test.runpytest(
        '-v',
        f'--testplan-csv={str(testplan_file.resolve())}',
        '--zephyr-base=.'
    )
    print(result.stdout)
    result.assert_outcomes(passed=3)
    result.stdout.fnmatch_lines_random([
        '*testcase.yaml::bluetooth.mesh.mesh_shell*qemu_cortex_m3*PASSED*',
        '*testcase.yaml::bluetooth.mesh.mesh_shell*qemu_x86*PASSED*',
        '*testcase.yaml::bluetooth.mesh.mesh_shell*nrf51dk_nrf51422*PASSED*',
        '*generated testplan file:*twister.csv*',
    ])

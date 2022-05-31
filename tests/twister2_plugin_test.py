from pathlib import Path

import pytest

TEST_DIR = Path(__file__).parent


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
        '*--zephyr-base=path*base directory for Zephyr*',
    ])


@pytest.mark.skip('WIP')
def test_twister(pytester):
    pytester.copy_example(str(TEST_DIR.joinpath('data/testcase.yaml')))
    pytester.copy_example(str(TEST_DIR.joinpath('data/device.log')))
    testplan_file = TEST_DIR.joinpath('twister.csv')
    result = pytester.runpytest(
        '-v',
        f'--testplan-csv={str(testplan_file.resolve())}',
        '--zephyr-base=.'
    )
    result.assert_outcomes(passed=3)
    result.stdout.fnmatch_lines_random([
        '*testcase.yaml::bluetooth.mesh.mesh_shell*qemu_cortex_m3*PASSED*',
        '*testcase.yaml::bluetooth.mesh.mesh_shell*qemu_x86*PASSED*',
        '*testcase.yaml::bluetooth.mesh.mesh_shell*nrf51dk_nrf51422*PASSED*',
        '*generated testplan file:*twister.csv*',
    ])

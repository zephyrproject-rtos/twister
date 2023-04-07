
import os
import textwrap

import pytest


def test_twister_help(pytester):
    result = pytester.runpytest('--help')
    result.stdout.fnmatch_lines_random([
        '*Twister reports:*',
        '*--testplan-csv=PATH*generate test plan in CSV format*',
        '*--testplan-json=PATH*generate test plan in JSON format*',
        '*--results-json=PATH*generate test results report in JSON format*',
        '*Twister:*',
        '*--twister*',
        '*--build-only*build only*',
        '*--platform=PLATFORM*build tests for specific platforms*',
        '*--board-root=PATH*directory to search for board configuration files*',
        '*--zephyr-base=PATH*base directory for Zephyr*',
        '*--quarantine-list=*',
        '*--clear={no,delete,archive}*',
        '*Clear twister artifacts*',
        '*--extra-args=EXTRA_ARGS*',
        '*Extra CMake arguments*',
        '*--overflow-as-errors*',
        '*--integration*',
        '*--emulation-only*',
        '*--arch=ARCH*',
        '*--all*',
        '*-M {pass,all}, --runtime-artifact-cleanup={pass,all}*',
        '*--prep-artifacts-for-testing*',
        '*--west-flash*',
        '*--west-runner*',
        '*--save-tests=PATH*',
        '*--load-tests=PATH*',
        '*--only-from-yaml*',
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


def test_if_regular_tests_work_with_specification_file(pytester, resources):
    pytester.copy_example(str(resources))
    test_file_content = textwrap.dedent("""
        import pytest

        @pytest.mark.build_specification
        def test_foo(builder):
            pass

        @pytest.mark.build_specification('scenario1', 'scenario2')
        def test_bar(builder):
            pass
    """)
    test_file = pytester.path / 'tests' / 'foobar_test.py'
    test_file.write_text(test_file_content)

    test_spec_content = textwrap.dedent("""
        common:
            timeout: 30
            harness: console
            harness_config:
                type: one_line
                regex:
                    - "Hello World! (.*)"
        tests:
            scenario1:
                tags: tag1
            scenario2:
                tags: tag1
            scenario3:
                tags: tag2
                platform_allow: mps2_an521_remote
    """)
    test_spec_file = pytester.path / 'tests' / 'testspec.yaml'
    test_spec_file.write_text(test_spec_content)

    result = pytester.runpytest(
        str(test_file),
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--collect-only',
        '-m not skip'
    )
    result.stdout.fnmatch_lines_random([
        '*<Module*tests/foobar_test.py>*',
        '*<Function*test_foo*native_posix:scenario1*>*',
        '*<Function*test_foo*native_posix:scenario2*>*',
        '*<Function*test_bar*native_posix:scenario1*>*',
        '*<Function*test_bar*native_posix:scenario2*>*',
    ])
    result.stdout.no_fnmatch_line(
        '*<Function*test_foo*native_posix:scenario3*>*',  # should be marked as skip
    )


def test_if_regular_tests_filter_platform_allow_from_spec_file(pytester, resources):
    pytester.copy_example(str(resources))
    test_file_content = textwrap.dedent("""
        import pytest

        @pytest.mark.build_specification
        def test_foo(builder):
            pass
    """)
    test_file = pytester.path / 'tests' / 'foobar_test.py'
    test_file.write_text(test_file_content)

    test_spec_content = textwrap.dedent("""
        tests:
            scenario1:
                tags: tag1
            scenario3:
                tags: tag2
                platform_allow: mps2_an521_remote
    """)
    test_spec_file = pytester.path / 'tests' / 'testspec.yaml'
    test_spec_file.write_text(test_spec_content)

    result = pytester.runpytest(
        str(test_file),
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--collect-only'
    )
    result.stdout.fnmatch_lines_random([
        '*<Module*tests/foobar_test.py>*',
        '*<Function*test_foo*native_posix:scenario1*>*'
    ])
    result.stdout.no_fnmatch_line(
        '*<Function*test_foo*native_posix:scenario3*>*',  # filtered by platform_allow
    )


def test_if_pytest_skip_twister_tests_if_not_enabled(pytester, resources) -> None:
    pytester.copy_example(str(resources))
    if os.path.exists('pytest.ini'):
        os.remove('pytest.ini')
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--co',
    )
    result.stdout.re_match_lines_random([
        r'collected 0 items',
    ])


def test_if_pytest_skip_twister_regular_tests_if_not_enabled(pytester, resources):
    pytester.copy_example(str(resources))
    if os.path.exists('pytest.ini'):
        os.remove('pytest.ini')
    test_file_content = textwrap.dedent("""
        import pytest

        @pytest.mark.build_specification
        def test_foo(builder):
            pass

        def test_bar():
            pass
    """)
    test_file = pytester.path / 'tests' / 'foobar_test.py'
    test_file.write_text(test_file_content)
    test_spec_content = textwrap.dedent("""
        tests:
            scenario1:
                tags: tag1
    """)
    test_spec_file = pytester.path / 'tests' / 'testspec.yaml'
    test_spec_file.write_text(test_spec_content)

    result = pytester.runpytest(
        str(test_file),
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--co',
        '-m not skip',
    )
    result.stdout.re_match_lines_random([
        '.*test_bar',
    ])
    result.stdout.no_fnmatch_line('.*test_foo')

    result = pytester.runpytest(
        str(test_file),
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '-v',
    )
    result.stdout.re_match_lines_random([
        '.*test_bar PASSED',
        '.*test_foo SKIPPED.*Twister is not enabled'
    ])


@pytest.mark.parametrize(
    ('extend_command, expected'),
    [
        (
            '--quarantine-verify',
            ['Exit: No quarantine list given to be verified*']
        ),
        (
            '--build-only --clear=no',
            ['Exit: To apply `--build-only` option*']
        ),
        (
            '--device-testing',
            ['Exit: Option `--device-testing` must be used with*'],
        ),
        (
            '--device-testing --device-serial=/dev/ACM0 --platform=A --platform=B',
            ['*only one platform is allowed*'],
        ),
        (
            '--device-testing --device-serial=/dev/ACM0',
            ['*platform must be provided*'],
        ),
        (
            '--device-serial=/dev/ACM0 --device-serial-pty=script.py',
            ['Exit: Not allowed to combine arguments:*']
        ),
        (
            '--west-flash=--erase',
            ['*must be used with `--device-testing`*']
        ),
        (
            '--west-runner=jlink',
            ['*must be used with `--device-testing`*']
        )
    ],
    ids=[
        'only_quarantine_verify',
        'build_only_with_clear',
        'only_device_testing',
        'device_serial_with_more_platforms',
        'device_serial_without_platform',
        'combined_with_device_serial',
        'west_flash',
        'west_runner'
    ]
)
def test_if_invalid_parameters_raises_error(pytester, resources, extend_command, expected):
    pytester.copy_example(str(resources))

    runpytest_args = [
        '--zephyr-base=.'
    ]
    if extend_command:
        runpytest_args.extend(extend_command.split(' '))
    result = pytester.runpytest(*runpytest_args)

    result.stderr.fnmatch_lines_random(expected)

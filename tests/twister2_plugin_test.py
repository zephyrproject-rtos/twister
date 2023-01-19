import textwrap


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
        '*--zephyr-base=PATH*base directory for Zephyr*',
        '*--quarantine-list=*',
        '*--clear={no,delete,archive}*',
        '*Clear twister artifacts*',
        '*--extra-args=EXTRA_ARGS*',
        '*Extra CMake arguments*',
        '*--overflow-as-errors*'
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
        '*5 tests collected*',
    ])
    result.stdout.no_fnmatch_line(
        '*<Function*test_foo*native_posix:scenario3*>*',  # should be marked as skip
    )

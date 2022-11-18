
import json
import textwrap

from pathlib import Path


def _get_test_scenario(tests, test_name):
    matched_scenarios = [scenario for scenario in tests if scenario['test_name'] == test_name]
    if not matched_scenarios:
        return None
    return matched_scenarios[0]


def test_if_pytest_use_quarantine_file(pytester, resources) -> None:
    """
    Run tests with quarantine list. Verify in test output json file
    if quarantine comment is added to proper test configuration
    """
    pytester.copy_example(str(resources))
    quarantine_file: Path = resources / 'quarantine' / 'helloworld_native.yml'
    output_testplan: Path = pytester.path / 'tesplan.json'
    pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--quarantine-list={quarantine_file}',
        f'--testplan-json={output_testplan}',
        '--co'
    )
    with open(output_testplan) as f:
        json_data = json.load(f)

    hello_qemu = _get_test_scenario(json_data['tests'], 'sample.basic.helloworld[qemu_cortex_m3]')
    assert hello_qemu
    assert not hello_qemu['quarantine']

    hello_native = _get_test_scenario(json_data['tests'], 'sample.basic.helloworld[native_posix]')
    assert hello_native
    assert 'link.to.issue' in hello_native['quarantine']


def test_if_pytest_use_two_quarantine_files(pytester, resources) -> None:
    """
    Run tests with two quarantine-list yaml files. Verify in test output
    json file if proper test configurations are marked.
    """
    pytester.copy_example(str(resources))
    quarantine_file1: Path = resources / 'quarantine' / 'helloworld_native.yml'
    quarantine_file2: Path = resources / 'quarantine' / 'filter_arch_and_plat.yml'
    output_testplan: Path = pytester.path / 'tesplan.json'
    pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--quarantine-list={quarantine_file1}',
        f'--quarantine-list={quarantine_file2}',
        f'--testplan-json={output_testplan}',
        '--co',
    )
    with open(output_testplan) as f:
        json_data = json.load(f)

    assert _get_test_scenario(json_data['tests'], 'sample.basic.helloworld[qemu_cortex_m3]')['quarantine']
    assert _get_test_scenario(json_data['tests'], 'sample.basic.helloworld[native_posix]')['quarantine']
    assert _get_test_scenario(json_data['tests'], 'xyz.common_merge_1[qemu_cortex_m3]')['quarantine']
    assert _get_test_scenario(json_data['tests'], 'xyz.common_merge_2[qemu_cortex_m3]')['quarantine']
    assert _get_test_scenario(json_data['tests'], 'xyz.common_merge_2[native_posix]')['quarantine']
    assert not _get_test_scenario(json_data['tests'], 'xyz.common_merge_1[native_posix]')['quarantine']


def test_if_pytest_handle_quarantine_verify(pytester, resources) -> None:
    """
    Verify if only tests under quarantine are collected
    """
    pytester.copy_example(str(resources))
    quarantine_file: Path = resources / 'quarantine' / 'helloworld_native.yml'
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--quarantine-list={quarantine_file}',
        '-m quarantine',
        '--co',
    )
    result.stdout.re_match_lines_random([
        r'.*sample.basic.helloworld\[native_posix\]>'
    ])
    result.stdout.no_re_match_line(r'.*sample.basic.helloworld\[qemu_cortex_m3\]>')


def test_quarantine_for_python_tests(pytester, tmp_path):
    quarantine_file = tmp_path / "quarantine.yml"
    quarantine_file.write_text(textwrap.dedent("""\
      - scenarios:
        - test_quarantine_1
        - test_quarantine_2
    """))
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest
            def test_quarantine_1():
                assert True

            def test_quarantine_2():
                assert True

            def test_no_quarantine():
                assert True
            """)
    )
    # quarantine tests should be skipped
    result = pytester.runpytest(
        '-v',
        '--zephyr-base=.',
        f'--quarantine-list={quarantine_file}'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=1, skipped=2)

    # only tests under quarantine should be run
    result = pytester.runpytest(
        '-v',
        '--zephyr-base=.',
        f'--quarantine-list={quarantine_file}',
        '-m quarantine'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=2, skipped=0)


import textwrap
from pathlib import Path

import pytest


def test_if_pytest_use_quarantine_file(pytester, resources) -> None:
    """
    Run tests with quarantine list. Verify test output
    """
    pytester.copy_example(str(resources))
    quarantine_file: Path = resources / 'quarantine' / 'helloworld_native.yml'
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--quarantine-list={quarantine_file}',
        '--co'
    )
    result.stdout.re_match_lines_random([
        r'.*sample.basic.helloworld\[qemu_cortex_m3\]*'
    ])
    result.stdout.no_re_match_line(r'.*sample.basic.helloworld\[native_posix\]*')

    # check if quarantine comment is found in output log
    with open(Path('twister-out/testcases_creation.log')) as f:
        assert 'link.to.issue' in f.read()


def test_if_pytest_use_regex_in_quarantine_files(pytester, resources) -> None:
    """
    Run tests with quarantine list. Verify if regex is processed
    """
    pytester.copy_example(str(resources))
    quarantine_file: Path = resources / 'quarantine' / 'regex_example.yml'
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--quarantine-list={quarantine_file}',
        '--co',
    )
    result.stdout.re_match_lines_random([
        r'.*sample.basic.helloworld\[qemu_cortex_m3\]*',
        r'.*sample.basic.helloworld\[native_posix\]*',
        r'.*xyz.common_merge_1\[native_posix\]*',

    ])
    result.stdout.no_re_match_line(r'.*xyz.common_merge_1\[qemu_cortex_m3\]*')
    result.stdout.no_re_match_line(r'.*xyz.common_merge_2\[qemu_cortex_m3\]*')


def test_if_pytest_use_two_quarantine_files(pytester, resources) -> None:
    """
    Run tests with two quarantine-list yaml files. Verify in test output
    json file if proper test configurations are marked.
    """
    pytester.copy_example(str(resources))
    quarantine_file1: Path = resources / 'quarantine' / 'helloworld_native.yml'
    quarantine_file2: Path = resources / 'quarantine' / 'filter_arch_and_plat.yml'
    result = pytester.runpytest(
        f'--zephyr-base={str(pytester.path)}',
        '--platform=native_posix',
        '--platform=qemu_cortex_m3',
        f'--quarantine-list={quarantine_file1}',
        f'--quarantine-list={quarantine_file2}',
        '--co',
    )
    result.stdout.re_match_lines_random([
        r'.*xyz.common_merge_1\[native_posix\]*'
    ])
    result.stdout.no_re_match_line(r'.*sample.basic.helloworld\[qemu_cortex_m3\]*')
    result.stdout.no_re_match_line(r'.*sample.basic.helloworld\[native_posix\]*')
    result.stdout.no_re_match_line(r'.*xyz.common_merge_1\[qemu_cortex_m3\]*')
    result.stdout.no_re_match_line(r'.*xyz.common_merge_2\[qemu_cortex_m3\]*')
    result.stdout.no_re_match_line(r'.*xyz.common_merge_2\[native_posix\]*')


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
        '--quarantine-verify',
        '--co',
    )
    result.stdout.re_match_lines_random([
        r'.*sample.basic.helloworld\[native_posix\]>'
    ])
    result.stdout.no_re_match_line(r'.*sample.basic.helloworld\[qemu_cortex_m3\]>')


@pytest.mark.skip('Quarnatine not supported for pytest scenarios without test specification')
def test_quarantine_for_python_tests(pytester, tmp_path):
    quarantine_file = tmp_path / 'quarantine.yml'
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
    result.assert_outcomes(passed=1)

    # only tests under quarantine should be run
    result = pytester.runpytest(
        '-v',
        '--zephyr-base=.',
        f'--quarantine-list={quarantine_file}',
        '--quarantine-verify'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=2)


def test_quarantine_for_empty_file(pytester, tmp_path):
    quarantine_file = tmp_path / 'quarantine.yml'
    quarantine_file.write_text(textwrap.dedent("""\
      # empty quarantine
    """))
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest
            def test_quarantine_1():
                assert True
            """)
    )
    result = pytester.runpytest(
        '-v',
        '--zephyr-base=.',
        f'--quarantine-list={quarantine_file}'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=1, skipped=0)

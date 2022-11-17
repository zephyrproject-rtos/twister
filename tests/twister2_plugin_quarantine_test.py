
import json
from pathlib import Path


def test_if_pytest_use_quarantine_file(pytester, resources) -> None:
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
        r'.*sample.basic.helloworld\[qemu_cortex_m3\]>',
        r'.*sample.basic.helloworld\[native_posix\]> skip'
    ])


def test_if_pytest_use_two_quarantine_files(pytester, resources) -> None:
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
        r'.*xyz.common_merge_1\[qemu_cortex_m3\]> skip',
        r'.*xyz.common_merge_1\[native_posix\]>',
        r'.*xyz.common_merge_2\[qemu_cortex_m3\]> skip',
        r'.*xyz.common_merge_2\[native_posix\]> skip',
        r'.*sample.basic.helloworld\[qemu_cortex_m3\]> skip',
        r'.*sample.basic.helloworld\[native_posix\]> skip'
    ])


def test_if_pytest_handle_quarantine_verify(pytester, resources) -> None:
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
    print(result.stdout)
    result.stdout.re_match_lines_random([
        r'.*sample.basic.helloworld\[native_posix\]>'
    ])
    result.stdout.no_re_match_line(r'.*sample.basic.helloworld\[qemu_cortex_m3\]>')


def test_if_pytest_generate_testplan_with_quarantine(pytester, resources) -> None:
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
    assert output_testplan.is_file()

    with open(output_testplan) as f:
        json_data = json.load(f)

    hello_qemu = _get_test_scenario(json_data['tests'], test_name='sample.basic.helloworld[qemu_cortex_m3]')
    assert hello_qemu
    assert 'skip_reason' not in hello_qemu

    hello_native = _get_test_scenario(json_data['tests'], test_name='sample.basic.helloworld[native_posix]')
    assert hello_native
    assert 'link.to.issue' in hello_native['skip_reason']


def _get_test_scenario(tests, test_name):
    matched_scenarios = [scenario for scenario in tests if scenario['test_name'] == test_name]
    if not matched_scenarios:
        return None
    return matched_scenarios[0]

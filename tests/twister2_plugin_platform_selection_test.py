import textwrap
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ('extend_command, expected, not_expected'),
    [
        (
            '--all',
            ['*native_posix*', '*qemu_cortex_m3*', '*altera_max10*'],
            ['*mps2_an521_remote*']
        ),
        (
            '--emulation-only',
            ['*native_posix*', '*qemu_cortex_m3*'],
            ['*altera_max10*', '*mps2_an521_remote*']
        ),
        (
            '--arch=arm',
            ['*qemu_cortex_m3*'],
            ['*native_posix*', '*altera_max10*', '*mps2_an521_remote*']
        ),
        (
            '--arch=posix --arch=nios2',
            ['*native_posix*', '*altera_max10*'],
            ['*qemu_cortex_m3*', '*mps2_an521_remote*']
        ),
        (
            '',
            ['*native_posix*'],
            ['*qemu_cortex_m3*', '*altera_max10*', '*mps2_an521_remote*']
        )
    ],
    ids=[
        'all-platforms',
        'emulation-only',
        'arch-arm',
        'select-two-archs',
        'default-platforms'
    ]
)
def test_if_selected_proper_platforms(
        pytester, resources, extend_command, expected, not_expected
):
    pytester.copy_example(str(resources))
    test_dir: Path = pytester.path / 'tests' / 'hello_world'
    runpytest_args = [
        f'--zephyr-base={str(pytester.path)}',
        '--collect-only',
        str(test_dir)
    ]
    if extend_command:
        runpytest_args.extend(extend_command.split(' '))
    result = pytester.runpytest(*runpytest_args)

    result.stdout.fnmatch_lines_random(expected)
    for no_line in not_expected:
        result.stdout.no_fnmatch_line(no_line)


@pytest.mark.parametrize(
    ('extend_command, expected, not_expected'),
    [
        (
            '',
            ['*altera_max10*'],
            ['*native_posix*', '*qemu_cortex_m3*', '*mps2_an521_remote*']
        ),
        (
            '--platform=native_posix',
            ['*native_posix*'],
            ['*altera_max10*', '*qemu_cortex_m3*', '*mps2_an521_remote*']
        ),
        (
            '--all',
            ['*native_posix*', '*qemu_cortex_m3*', '*altera_max10*'],
            ['*mps2_an521_remote*']
        )
    ],
    ids=[
        'platform-from-hardware-map',
        'platform-from-command',
        'all-platforms'
    ]
)
def test_if_selected_proper_platform_with_hardware_map(
        pytester, resources, extend_command, expected, not_expected
):
    pytester.copy_example(str(resources))
    hardware_map = pytester.path / 'hardware_map.yml'
    hardware_map.write_text(textwrap.dedent("""\
        - available: true
          connected: true
          id: 01234
          platform: altera_max10
          runner: jlink
          serial: /dev/ttyACM0
        - available: true
          connected: true
          id: 01234
          platform: altera_max10
          runner: jlink
          serial: /dev/ttyACM1
    """))
    test_dir: Path = pytester.path / 'tests' / 'hello_world'
    runpytest_args = [
        f'--zephyr-base={str(pytester.path)}',
        '--collect-only',
        '--device-testing',
        f'--hardware-map={hardware_map}',
        str(test_dir)
    ]
    if extend_command:
        runpytest_args.extend(extend_command.split(' '))
    result = pytester.runpytest(*runpytest_args)

    result.stdout.fnmatch_lines_random(expected)
    for no_line in not_expected:
        result.stdout.no_fnmatch_line(no_line)

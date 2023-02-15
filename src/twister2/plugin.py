from __future__ import annotations

import datetime
import logging
import os
import shutil
from pathlib import Path

import pytest

from twister2.filter.filter_plugin import FilterPlugin
from twister2.filter.tag_filter import TagFilter
from twister2.generate_tests_plugin import GenerateTestPlugin
from twister2.load_tests import LoadTestPlugin
from twister2.log import configure_logging
from twister2.platform_specification import search_platforms
from twister2.twister_config import TwisterConfig
from twister2.yaml_file import YamlPytestPlugin

logger = logging.getLogger(__name__)

pytest_plugins = (
    'twister2.fixtures.builder',
    'twister2.fixtures.dut',
    'twister2.fixtures.fixtures',
    'twister2.fixtures.log_parser',
    'twister2.report.test_plan_plugin',
    'twister2.report.test_results_plugin',
    'twister2.report.yaml_test_reporting_plugin',
)


def pytest_addoption(parser: pytest.Parser):
    twister_group = parser.getgroup('Twister')
    twister_group.addoption(
        '--twister',
        action='store_true',
        default=False,
        help='Activate twister plugin'
    )
    parser.addini(
        'twister',
        'Activate twister plugin',
        type='bool'
    )
    twister_group.addoption(
        '--build-only',
        default=False,
        action='store_true',
        help='build only'
    )
    twister_group.addoption(
        '--platform',
        action='append',
        help='build tests for specific platforms'
    )
    twister_group.addoption(
        '--all',
        action='store_true',
        help='Build/test on all platforms. Any --platform arguments '
             'will be ignored'
    )
    twister_group.addoption(
        '--board-root',
        metavar='PATH',
        action='append',
        default=None,
        help='directory to search for board configuration files'
    )
    parser.addini(
        'board_root',
        type='pathlist',
        help='directories to search for Zephyr board configuration files',
    )
    twister_group.addoption(
        '--zephyr-base',
        metavar='PATH',
        action='store',
        default=None,
        help='base directory for Zephyr'
    )
    parser.addini(
        'zephyr_base',
        type='string',
        help='base directory for Zephyr',
    )
    twister_group.addoption(
        '-O',
        '--outdir',
        metavar='PATH',
        dest='output_dir',
        default='twister-out',
        help='output directory for logs and binaries (default: %(default)s)'
    )
    twister_group.addoption(
        '--device-testing',
        dest='device_testing',
        action='store_true',
        help='Test on device directly. Specify the serial device to '
             'use with the --device-serial option.'
    )
    twister_group.addoption(
        '--hardware-map',
        metavar='PATH',
        help='load hardware map from a file'
    )
    twister_group.addoption(
        '--device-serial',
        help='Serial device for accessing the board '
             '(e.g., /dev/ttyACM0)'
    )
    twister_group.addoption(
        '--device-serial-baud',
        default=115200,
        help='Serial device baud rate (default 115200)'
    )
    twister_group.addoption(
        '--device-serial-pty',
        metavar='PATH',
        help='Script for controlling pseudoterminal. '
             'E.g --device-testing --device-serial-pty=<script>'
    )
    twister_group.addoption(
        '--west-flash',
        action='store',
        help='Extend parameters for west flash. '
             'E.g. -device-testing -west-flash="--board-id=foobar,--erase" '
             'will translate to "west flash -- --board-id=foobar --erase"'
    )
    twister_group.addoption(
        '--west-runner',
        action='store',
        help='use the specified west runner. E.g. --west-runner=pyocd'
    )
    twister_group.addoption(
        '-G', '--integration',
        action='store_true',
        help='Run integration tests',
    )
    twister_group.addoption(
        '--emulation-only',
        action='store_true',
        help='Only build and run emulation platforms',
    )
    twister_group.addoption(
        '--arch',
        action='append',
        help='Arch filter for testing'
    )
    twister_group.addoption(
        '--tags',
        action='append',
        help='filter test by tags, e.g.: --tags=@tag1,~@tag2 --tags=@tag3'
    )
    twister_group.addoption(
        '-S', '--enable-slow',
        dest='enable_slow',
        action='store_true',
        help='Execute time-consuming test cases that have been marked '
             'as "slow" in testcase.yaml. Normally these are only built.',
    )
    twister_group.addoption(
        '--quarantine-list',
        dest='quarantine_list_path',
        metavar='FILENAME',
        action='append',
        help='Load list of test scenarios under quarantine. These scenarios '
             'will be skipped with quarantine as the reason.'
    )
    twister_group.addoption(
        '--quarantine-verify',
        action='store_true',
        help='Run only tests selected with --quarantine-list'
    )
    twister_group.addoption(
        '--clear',
        dest='clear',
        action='store',
        default='archive',
        choices=('no', 'delete', 'archive'),
        help='Clear twister artifacts. '
             '"no" - use previous artifacts, '
             '"delete" - delete previous artifacts, '
             '"archive" - keep previous artifacts '
             '(default=%(default)s)'
    )
    twister_group.addoption(
        '--builder',
        dest='builder',
        action='store',
        default='cmake',
        choices=('cmake', 'west'),
        help='Select builder type (default=%(default)s)'
    )
    twister_group.addoption(
        '-X', '--fixture',
        dest='fixtures',
        action='append',
        default=[],
        help='Specify a fixture that a test setup is supporting.'
    )
    twister_group.addoption(
        '--extra-args',
        default=[],
        action='append',
        help='Extra CMake arguments which will be passed to CMake during '
             'building. May be called multiple times. The key-value entries '
             'will be prefixed with -D before being passed to CMake. '
             'For example: '
             'pytest --extra-args=USE_CCACHE=0 '
             'will be translated to '
             'cmake -DUSE_CCACHE=0'
    )
    twister_group.addoption(
        '--overflow-as-errors',
        default=False,
        action='store_true',
        help='Treat memory overflows as errors.'
    )
    twister_group.addoption(
        '-M', '--runtime-artifact-cleanup',
        choices=('pass', 'all'),
        help='Cleanup test artifacts. "pass" option only removes artifacts of '
             'passing or skipping tests. If you wish to remove all artifacts '
             'including those of failed tests, use "all".'
    )
    twister_group.addoption(
        '--prep-artifacts-for-testing',
        default=False,
        action='store_true',
        help='Prepare artifacts for testing - remove unnecessary files after '
             'application building and keep only this one which are crucial to '
             'run tests. Additionally sanitize those files from local Zephyr '
             'base paths to be able to use those artifacts on another host/'
             'computer/server.'
    )
    twister_group.addoption(
        '--save-tests',
        dest='save_tests_path',
        metavar='PATH',
        action='store',
        default=None,
        help='save test plan and exit'
    )
    twister_group.addoption(
        '--load-tests',
        dest='load_tests_path',
        metavar='PATH',
        action='store',
        default=None,
        help='load testplan from file'
    )
    twister_group.addoption(
        '--only-failed',
        dest='only_failed',
        action='store_true',
        help='Run only those tests that failed the previous twister run invocation.'
    )
    # twister_group.addoption(
    #     '--test-only',
    #     dest='test_only',
    #     action='store_true',
    #     help='Only run device tests with current artifacts, do not build the code'
    # )
    twister_group.addoption(
        '--only-from-yaml',
        dest='only_from_yaml',
        action='store_true',
        help='Run only tests generated from yaml files. Do not collect pytest scenarios'
    )


def pytest_configure(config: pytest.Config):
    if config.getoption('help'):
        return

    register_custom_markers(config)

    if not (config.getoption('twister') or config.getini('twister')):
        return

    zephyr_base = os.path.expanduser(
        config.getoption('zephyr_base') or config.getini('zephyr_base') or os.environ.get('ZEPHYR_BASE', '')
    )
    if not zephyr_base:
        pytest.exit(
            'Path to Zephyr directory must be provided as pytest argument or in environment variable: ZEPHYR_BASE'
        )

    validate_options(config)
    update_load_tests_path(config)

    config.option.output_dir = _normalize_path(config.option.output_dir)

    # Export zephyr_base variable so other tools like west would also use the same one
    os.environ['ZEPHYR_BASE'] = zephyr_base

    xdist_worker = hasattr(config, 'workerinput')  # xdist worker

    if not xdist_worker:
        run_artifactory_cleanup(config)

    # create output directory if not exists
    os.makedirs(config.option.output_dir, exist_ok=True)

    configure_logging(config)

    # register plugins
    config.pluginmanager.register(plugin=TwisterExtPlugin(), name='twister ext plugin')
    config.pluginmanager.register(plugin=LoadTestPlugin(), name='load test plugin')
    config.pluginmanager.register(plugin=YamlPytestPlugin(), name='yaml file plugin')
    config.pluginmanager.register(plugin=GenerateTestPlugin(), name='generate tests plugin')

    filter_plugin = FilterPlugin(config)
    if config.getoption('tags'):
        filter_plugin.add_filter(TagFilter(config))
    config.pluginmanager.register(plugin=filter_plugin, name='filter_tests')

    # configure twister
    logger.debug('ZEPHYR_BASE: %s', zephyr_base)

    board_root = config.option.board_root or config.getini('board_root')

    config._platforms = search_platforms(zephyr_base, board_root)  # type: ignore
    config.twister_config = TwisterConfig.create(config)  # type: ignore


def register_custom_markers(config: pytest.Config) -> None:
    # register custom markers for twister
    markers = [
        'tags(tag1, tag2, ...): mark test for specific tags',
        'platform(platform_name): mark test for specific platform',
        'type(test_type): mark test for specific type',
        'slow: mark test as slow',
        'build_only: test can only be built',
        'build_specification(names="scenario1,scenario2"): select scenarios to build',
    ]
    for marker in markers:
        config.addinivalue_line('markers', marker)


def validate_options(config: pytest.Config) -> None:
    """Verify if user provided proper options"""
    if config.option.device_testing and not (
            config.option.hardware_map
            or config.option.device_serial
            or config.option.device_serial_pty
    ):
        pytest.exit(
            'Option `--device-testing` must be used with `--hardware-map` '
            'or `--device-serial` or `--device-serial-pty`.'
        )
    if config.option.device_testing and \
            (config.option.device_serial or config.option.device_serial_pty):
        if not config.option.platform:
            pytest.exit(
                'When `--device-testing` is used with `--device-serial` or '
                '`--device-serial-pty`, a platform must be provided.'
            )
        elif len(config.option.platform) > 1:
            pytest.exit(
                'When `--device-testing` is used with `--device-serial` or '
                '`--device-serial-pty`, only one platform is allowed.'
            )
    if ([
        bool(config.option.hardware_map),
        bool(config.option.device_serial),
        bool(config.option.device_serial_pty)
    ].count(True) > 1):
        pytest.exit(
            'Not allowed to combine arguments: `--hardware-map`, `--device-serial` '
            'and `--device-serial-pty`.'
        )
    if config.option.build_only and config.option.clear == 'no':
        pytest.exit(
            'To apply `--build-only` option, `--clear` option cannot be set as `no`.'
        )
    if config.option.quarantine_verify and not config.option.quarantine_list_path:
        pytest.exit(
            'No quarantine list given to be verified. '
            'Option `--quarantine-verify` must be used with `--quarantine-list`.'
        )
    if (config.option.west_flash or config.option.west_runner) \
            and not config.option.device_testing:
        pytest.exit(
            'Options `--west-flash` or `--west-runner` must be used with `--device-testing`.'
        )


def run_artifactory_cleanup(config: pytest.Config) -> None:
    """Clean, archive or delete an output dir. If load test file
    is in impacted directory, backup them or update path"""
    if any([
        os.path.exists(config.option.output_dir) is False,
        config.option.collectonly,
        config.option.save_tests_path
    ]):
        return

    choice = config.option.clear
    output_dir = config.option.output_dir
    if choice == 'no':
        print('Keeping previous artifacts untouched')
    elif choice == 'delete':
        load_tests_content = store_load_tests_file_content(config)
        print(f'Deleting previous artifacts from {output_dir}')
        shutil.rmtree(output_dir, ignore_errors=True)
        restore_load_tests_file(config, load_tests_content)
    elif choice == 'archive':
        timestamp = os.path.getmtime(output_dir)
        file_date = datetime.datetime.fromtimestamp(timestamp).strftime('%y%m%d%H%M%S')
        new_output_dir = f'{output_dir}_{file_date}'
        print(f'Renaming output directory to {new_output_dir}')
        shutil.move(str(output_dir), new_output_dir)
        update_load_tests_path_if_archieved(config, new_output_dir)


def update_load_tests_path(config: pytest.Config) -> None:
    """Update load tests path if using `only-failed` option. Normalize and validate"""
    if config.option.only_failed:
        if not config.option.load_tests_path:
            config.option.load_tests_path = str(os.path.join(config.option.output_dir, 'twister.json'))
    if config.option.load_tests_path:
        config.option.load_tests_path = _normalize_path(config.option.load_tests_path)
        load_tests = Path(config.option.load_tests_path)
        if not load_tests.is_file():
            pytest.exit(f'File {load_tests} does not exists.')
    # --collect only should be set to exit pytest just after collecting tests (works with xdist)
    if config.option.save_tests_path:
        config.option.collectonly = True


def update_load_tests_path_if_archieved(config: pytest.Config, new_output_dir: str) -> None:
    if not config.option.load_tests_path:
        return
    load_tests = Path(config.option.load_tests_path)
    if str(load_tests.parent) == config.option.output_dir:
        config.option.load_tests_path = _normalize_path(
            Path(new_output_dir) / load_tests.name
        )


def store_load_tests_file_content(config: pytest.Config) -> None | str:
    if not config.option.load_tests_path:
        return None
    load_tests = Path(config.option.load_tests_path)
    if str(load_tests.parent) == config.option.output_dir:
        with open(load_tests, 'r') as fp:
            return fp.read()
    return None


def restore_load_tests_file(config: pytest.Config, load_tests_content: str | None) -> None:
    if not load_tests_content:
        return
    os.makedirs(config.option.output_dir, exist_ok=True)
    with open(config.option.load_tests_path, 'w') as fp:
        fp.write(load_tests_content)


def _normalize_path(path: str | Path) -> str:
    path = os.path.expanduser(os.path.expandvars(path))
    path = os.path.normpath(os.path.abspath(path))
    return path


class TwisterExtPlugin():

    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        # extend JUnitXML report for user properties
        if marker := item.get_closest_marker('type'):
            item.user_properties.append(('type', marker.args[0]))
        if marker := item.get_closest_marker('tags'):
            item.user_properties.append(('tags', ' '.join(marker.args)))
        if marker := item.get_closest_marker('platform'):
            item.user_properties.append(('platform', marker.args[0]))

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_makereport(self, item, call):
        """
        Hook used to store information about failed test, which can be used in
        fixture's teardown. Example of use in fixture:
        test_failed = getattr(request.node, '_test_failed', False)
        """
        outcome = yield
        report = outcome.get_result()
        if report.failed:
            setattr(item, '_test_failed', True)
        return report


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
):
    """
    If Twister plugin is not enabled, then mark `build_specification` tests
    as skipped.
    """
    if hasattr(config, 'twister_config'):
        return

    for item in items:
        if item.get_closest_marker('build_specification'):
            item.add_marker(pytest.mark.skip('Twister is not enabled'))

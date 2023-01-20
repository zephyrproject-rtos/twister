from __future__ import annotations

import datetime
import logging
import os
import shutil
from pathlib import Path

import pytest

from twister2.filter.filter_plugin import FilterPlugin
from twister2.filter.tag_filter import TagFilter
from twister2.log import configure_logging
from twister2.platform_specification import search_platforms
from twister2.quarantine_plugin import QuarantinePlugin
from twister2.twister_config import TwisterConfig
from twister2.yaml_file import YamlModule

SAMPLE_FILENAME: str = 'sample.yaml'
TESTCASE_FILENAME: str = 'testcase.yaml'

logger = logging.getLogger(__name__)

pytest_plugins = (
    'twister2.fixtures.builder',
    'twister2.fixtures.dut',
    'twister2.fixtures.fixtures',
    'twister2.fixtures.log_parser',
    'twister2.generate_tests_plugin',
    'twister2.report.test_plan_plugin',
    'twister2.report.test_results_plugin',
)


def pytest_collect_file(parent, path):
    # discovers all yaml tests in test directory
    if path.basename in (SAMPLE_FILENAME, TESTCASE_FILENAME):
        return YamlModule.from_parent(parent, path=Path(path))


def pytest_addoption(parser: pytest.Parser):
    twister_group = parser.getgroup('Twister')
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
        help='load hardware map from a file',
    )
    twister_group.addoption(
        '--tags',
        action='append',
        help='filter test by tags, e.g.: --tags=@tag1,~@tag2 --tags=@tag3'
    )
    twister_group.addoption(
        '--enable-slow',
        dest='enable_slow',
        action='store_true',
        help='include slow tests',
    )
    twister_group.addoption(
        '--quarantine-list',
        dest='quarantine_list_path',
        metavar='FILENAME',
        action='append',
        help='Load list of test scenarios under quarantine. These scenarios '
             'will be skipped with quarantine as the reason. '
             'To verify their current status, one can run only quarantined tests '
             'using mark: -m quarantine'
    )
    twister_group.addoption(
        '--clear',
        dest='clear',
        action='store',
        default='no',
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
        default='west',
        choices=('west', 'cmake'),
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


def pytest_configure(config: pytest.Config):
    if config.getoption('help'):
        return

    zephyr_base = os.path.expanduser(
        config.getoption('zephyr_base') or config.getini('zephyr_base') or os.environ.get('ZEPHYR_BASE', '')
    )
    if not zephyr_base:
        pytest.exit(
            'Path to Zephyr directory must be provided as pytest argument or in environment variable: ZEPHYR_BASE'
        )

    validate_options(config)

    output_dir = config.option.output_dir

    # Export zephyr_base variable so other tools like west would also use the same one
    os.environ['ZEPHYR_BASE'] = zephyr_base

    xdist_worker = hasattr(config, 'workerinput')  # xdist worker

    if not config.option.collectonly and not xdist_worker:
        choice = config.option.clear
        if config.option.build_only and choice == 'no':
            msg = 'To apply "--build-only" option, "--clear" option cannot be set as "no".'
            logger.error(msg)
            pytest.exit(msg)
        run_artifactory_cleanup(choice, output_dir)

    # create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)

    configure_logging(config)

    # register plugins
    filter_plugin = FilterPlugin(config)
    if config.getoption('tags'):
        filter_plugin.add_filter(TagFilter(config))

    if not xdist_worker:
        config.pluginmanager.register(
            plugin=filter_plugin,
            name='filter_tests'
        )

    if config.getoption('quarantine_list_path'):
        quarantine_plugin = QuarantinePlugin(config)
        if not xdist_worker:
            config.pluginmanager.register(
                plugin=quarantine_plugin,
                name='quarantine'
            )

    # configure twister
    logger.debug('ZEPHYR_BASE: %s', zephyr_base)

    board_root = config.option.board_root or config.getini('board_root')

    config._platforms = search_platforms(zephyr_base, board_root)  # type: ignore
    config.twister_config = TwisterConfig.create(config)  # type: ignore

    # register custom markers for twister
    markers = [
        'tags(tag1, tag2, ...): mark test for specific tags',
        'platform(platform_name): mark test for specific platform',
        'type(test_type): mark test for specific type',
        'slow: mark test as slow',
        'build_only: test can only be built',
        'quarantine: mark test under quarantine. This mark is added dynamically after parsing '
        'quarantine-list-yaml file. To mark scenario in code better use skip/skipif',
    ]
    for marker in markers:
        config.addinivalue_line('markers', marker)


def validate_options(config: pytest.Config) -> None:
    """Verify if user provided proper options"""
    if config.option.device_testing and not config.option.hardware_map:
        pytest.exit(
            'Option `--device-testing` must be used with `--hardware-map`,.'
        )


def run_artifactory_cleanup(choice: str, output_dir: str | Path) -> None:
    if os.path.exists(output_dir) is False:
        return
    elif choice == 'no':
        print('Keeping previous artifacts untouched')
    elif choice == 'delete':
        print(f'Deleting previous artifacts from {output_dir}')
        shutil.rmtree(output_dir, ignore_errors=True)
    elif choice == 'archive':
        timestamp = os.path.getmtime(output_dir)
        file_date = datetime.datetime.fromtimestamp(timestamp).strftime('%y%m%d%H%M%S')
        new_output_dir = f'{output_dir}_{file_date}'
        print(f'Renaming output directory to {new_output_dir}')
        shutil.move(str(output_dir), new_output_dir)


def pytest_runtest_setup(item: pytest.Item) -> None:
    # extend JUnitXML report for user properties
    if marker := item.get_closest_marker('type'):
        item.user_properties.append(('type', marker.args[0]))
    if marker := item.get_closest_marker('tags'):
        item.user_properties.append(('tags', ' '.join(marker.args)))
    if marker := item.get_closest_marker('platform'):
        item.user_properties.append(('platform', marker.args[0]))

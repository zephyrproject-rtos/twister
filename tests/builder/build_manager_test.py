import copy
import os
import threading
import time
from contextlib import contextmanager
from unittest import mock

import pytest

from twister2.builder.build_manager import BuildManager, BuildStatus
from twister2.exceptions import (
    TwisterBuildException,
    TwisterBuildSkipException,
    TwisterMemoryOverflowException,
)


class MockBuilder(mock.Mock):
    def build(self):
        return


@pytest.fixture
def mocked_builder():
    return MockBuilder()


@pytest.fixture
def build_manager(build_config, mocked_builder) -> BuildManager:
    build_manager = BuildManager(build_config, mocked_builder, wait_build_timeout=2)
    return build_manager


@pytest.fixture
def generate_output_files(build_manager):
    build_dir = build_manager.build_config.build_dir

    base_dirs: list[str] = [
        'app',
        'CMakeFiles',
        'Kconfig',
        'modules',
        'twister',
        'zephyr'
    ]

    for base_dir in base_dirs:
        os.mkdir(build_dir / base_dir)

    files_to_create: list[str] = []

    base_files: list[str] = [
        'handler.log',
        'build.log',
        'build.ninja',
        'CMakeCache.txt',
        'cmake_install.cmake',
        'compile_commands.json',
        'device.log',
        'Makefile',
        'recording.csv',
        'zephyr_modules.txt',
        'zephyr_settings.txt',
    ]
    files_to_create += base_files

    cmakefiles_files: list[str] = [
        'CMakeOutput.log',
        'rules.ninja'
    ]
    cmakefiles_files = [os.path.join('CMakeFiles', file) for file in cmakefiles_files]
    files_to_create += cmakefiles_files

    files_to_create += [os.path.join('twister', 'testsuite_extra.conf')]

    zephyr_files: list[str] = [
        'cmake_install.cmake',
        'dev_handles.c',
        'dts.cmake',
        'edt.pickle',
        'libzephyr.a',
        'linker_zephyr_pre0.cmd',
        'linker_zephyr_pre0.cmd.dep',
        'linker_zephyr_pre1.cmd',
        'linker_zephyr_pre1.cmd.dep',
        'zephyr.bin',
        'zephyr.dts',
        'zephyr.elf',
        'zephyr.exe',
        'zephyr.hex',
        'zephyr.lst',
        'zephyr.map',
        'zephyr.stat',
        '.config'
    ]
    zephyr_files = [os.path.join('zephyr', file) for file in zephyr_files]
    files_to_create += zephyr_files

    for file_name in files_to_create:
        with open(build_dir / file_name, 'a'):
            pass


@contextmanager
def run_job_in_thread(job):
    # used to simplified test code
    t = threading.Thread(target=job, daemon=True)
    t.start()
    yield
    t.join()


def test_if_status_can_be_updated(build_manager):
    build_manager.update_status(BuildStatus.DONE)
    assert build_manager.get_status() == BuildStatus.DONE


def test_if_status_was_updated_after_build(build_manager):
    build_manager.update_status(BuildStatus.NOT_DONE)

    build_manager.build()
    assert build_manager.get_status() == BuildStatus.DONE


def test_if_status_was_set_as_skipped_after_build_memory_overflow(build_manager):
    build_manager.update_status(BuildStatus.NOT_DONE)

    def mocked_build_generator():
        raise TwisterMemoryOverflowException

    build_manager.builder.run_build_generator = mocked_build_generator
    with pytest.raises(TwisterMemoryOverflowException):
        build_manager.build()
    assert build_manager.get_status() == BuildStatus.SKIPPED


def test_if_status_was_set_as_failed_after_build_memory_overflow(build_manager):
    build_manager.update_status(BuildStatus.NOT_DONE)

    def mocked_build_generator():
        raise TwisterMemoryOverflowException

    build_manager.builder.run_build_generator = mocked_build_generator
    build_manager.build_config.overflow_as_errors = True
    with pytest.raises(TwisterMemoryOverflowException):
        build_manager.build()
    assert build_manager.get_status() == BuildStatus.FAILED


def test_if_build_manager_is_waiting_for_finish_another_build(build_manager, monkeypatch):
    build_manager_2 = copy.deepcopy(build_manager)
    _wait_for_build_to_finish = mock.MagicMock()
    monkeypatch.setattr(build_manager, '_wait_for_build_to_finish', _wait_for_build_to_finish)
    build_manager_2.update_status(BuildStatus.IN_PROGRESS)

    build_manager.build()
    assert build_manager.get_status() == BuildStatus.IN_PROGRESS
    _wait_for_build_to_finish.assert_called_once()


def test_if_test_is_failed_when_build_status_was_failed(build_manager):
    build_manager.update_status(BuildStatus.FAILED)

    expected_msg = f'Found in .*twister_builder.json the build status is set as {BuildStatus.FAILED} ' \
                   f'for: {build_manager.build_config.build_dir}'
    with pytest.raises(TwisterBuildException, match=expected_msg):
        build_manager.build()


def test_if_update_status_detect_properly_that_status_was_already_set(build_manager):
    build_manager_2 = copy.deepcopy(build_manager)
    status = build_manager.get_status()
    assert status == BuildStatus.NOT_DONE
    status = build_manager_2.get_status()
    assert status == BuildStatus.NOT_DONE

    assert build_manager.update_status(BuildStatus.IN_PROGRESS)
    assert not build_manager_2.update_status(BuildStatus.IN_PROGRESS)


def test_if_build_manager_does_not_build_when_source_is_already_built(
        build_manager, monkeypatch
):
    _wait_for_build_to_finish = mock.MagicMock()
    _build = mock.MagicMock()
    monkeypatch.setattr(build_manager, '_wait_for_build_to_finish', _wait_for_build_to_finish)
    monkeypatch.setattr(build_manager, '_build', _build)
    build_manager.update_status(BuildStatus.DONE)

    build_manager.build()
    assert build_manager.get_status() == BuildStatus.DONE
    _wait_for_build_to_finish.assert_not_called()
    _build.assert_not_called()


def test_if_build_manager_waits_until_status_is_changed_to_done(
        build_manager, mocked_builder, build_config
):
    """
    Building source code is ongoing by one process.
    Another process starts building same source code, and because build status is
    `IN_PROGRESS` second process waits for first process to finish building.
    While first process finished building second process should leave waiting loop.
    The build status should be updated by build manager to `DONE`.
    """
    build_manager.update_status(BuildStatus.IN_PROGRESS)

    def update_status():
        time.sleep(0.1)
        build_manager.update_status(BuildStatus.DONE)

    with run_job_in_thread(update_status):
        start_time = time.time()
        build_manager.build()
        finish_time = time.time()
    assert build_manager.get_status() == BuildStatus.DONE
    assert finish_time - start_time < 2  # Should not wait longer than 1 second


def test_if_build_manager_waits_until_status_is_changed_to_failed(build_manager):
    build_manager.update_status(BuildStatus.IN_PROGRESS)

    def update_status():
        time.sleep(0.1)
        build_manager.update_status(BuildStatus.FAILED)

    expected_msg = f'Found in .*twister_builder.json the build status is set as ' \
                   f'{BuildStatus.FAILED} for: {build_manager.build_config.build_dir}'
    with run_job_in_thread(update_status):
        with pytest.raises(TwisterBuildException, match=expected_msg):
            build_manager.build()
    assert build_manager.get_status() == BuildStatus.FAILED


def test_if_build_manager_waits_until_status_is_changed_to_skip(build_manager):
    build_manager.update_status(BuildStatus.IN_PROGRESS)

    def update_status():
        time.sleep(0.1)
        build_manager.update_status(BuildStatus.SKIPPED)

    expected_msg = f'Found in .*twister_builder.json the build status is set as ' \
                   f'{BuildStatus.SKIPPED} for: {build_manager.build_config.build_dir}'
    with run_job_in_thread(update_status):
        with pytest.raises(TwisterBuildSkipException, match=expected_msg):
            build_manager.build()
    assert build_manager.get_status() == BuildStatus.SKIPPED


def test_if_build_manager_waits_until_timed_out(build_manager):
    build_manager.update_status(BuildStatus.IN_PROGRESS)
    build_manager.wait_build_timeout = 1
    expected_msg = f'Timed out waiting for another thread to finish building: ' \
                   f'{build_manager.build_config.build_dir}'
    with pytest.raises(TwisterBuildException, match=expected_msg):
        build_manager.build()


@pytest.mark.parametrize(
    ('cleanup_method, additional_files_to_keep'),
    [
        (
            'cleanup_artifacts',
            [],
        ),
        (
            'prepare_device_testing_artifacts',
            [
                os.path.join('zephyr', 'zephyr.bin'),
                os.path.join('zephyr', 'zephyr.elf'),
                os.path.join('zephyr', 'zephyr.hex'),
            ],
        ),
    ],
    ids=[
        'basic_cleanup',
        'prepare_device_testing_artifacts',
    ]
)
def test_if_cleanup_artifacts_remove_files_properly(
        build_manager, generate_output_files, cleanup_method, additional_files_to_keep
):
    build_dir = build_manager.build_config.build_dir
    cleanup_method = getattr(build_manager, cleanup_method)
    cleanup_method()
    expected_files_to_keep = build_manager._basic_files_to_keep.copy()
    expected_files_to_keep += additional_files_to_keep
    expected_files_to_keep = [os.path.join(build_dir, file) for file in expected_files_to_keep]
    expected_files_to_keep = set(expected_files_to_keep)

    for dirpath, dirnames, filenames in os.walk(build_dir, topdown=False):
        for name in filenames:
            path = os.path.join(dirpath, name)
            assert path in expected_files_to_keep
            expected_files_to_keep.remove(path)

        for dir in dirnames:
            path = os.path.join(dirpath, dir)
            assert os.listdir(path)

    assert len(expected_files_to_keep) == 0


def test_if_sanitize_output_paths_works_properly(build_manager):
    file_to_sanitize = os.path.join(build_manager.build_config.build_dir, 'to_sanitize.txt')
    path_to_keep = os.path.join('samples', 'hello_world')
    full_path = os.path.join(build_manager.build_config.zephyr_base, path_to_keep)
    with open(file_to_sanitize, 'w') as file:
        file.write(full_path)

    files_to_sanitize = [file_to_sanitize]
    build_manager._sanitize_output_paths(files_to_sanitize)

    with open(file_to_sanitize, 'r') as file:
        assert file.read() == path_to_keep

import copy
import threading
import time
from contextlib import contextmanager
from unittest import mock

import pytest

from twister2.builder.build_filter_processor import BuildFilterProcessor
from twister2.builder.build_manager import BuildManager, BuildStatus
from twister2.builder.builder_abstract import BuildConfig
from twister2.exceptions import (
    TwisterBuildException,
    TwisterBuildSkipException,
    TwisterMemoryOverflowException,
)


class MockBuilder(mock.Mock):
    def build(self):
        return


class MockBuildFilterProcessor(BuildFilterProcessor):
    def apply_cmake_filtration(self, build_config: BuildConfig):
        pass


@pytest.fixture
def mocked_builder():
    return MockBuilder()


@pytest.fixture
def build_manager(build_config, mocked_builder) -> BuildManager:
    build_manager = BuildManager(build_config, mocked_builder, wait_build_timeout=2)
    return build_manager


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

import threading
import time
from contextlib import contextmanager
from unittest import mock

import pytest

from twister2.builder.build_manager import BuildManager, BuildStatus
from twister2.exceptions import TwisterBuildException

BUILD_DIR = 'build'


class MockBuilder(mock.Mock):
    def build(self, build_config):
        return


@pytest.fixture
def mocked_builder():
    return MockBuilder()


@pytest.fixture
def build_manager(tmp_path) -> BuildManager:
    build_manager = BuildManager(tmp_path, wait_build_timeout=2)
    return build_manager


@contextmanager
def run_job_in_thread(job):
    # used to simplified test code
    t = threading.Thread(target=job, daemon=True)
    t.start()
    yield
    t.join()


def test_if_status_can_be_updated(build_manager):
    build_manager.update_status('build_dir_1', BuildStatus.DONE)
    assert build_manager.get_status('build_dir_1') == BuildStatus.DONE


def test_if_status_was_updated_after_build(build_manager, build_config):
    mocked_builder = MockBuilder()
    build_manager.update_status(BUILD_DIR, BuildStatus.NOT_DONE)

    build_manager.build(builder=mocked_builder, build_config=build_config)
    assert build_manager.get_status(BUILD_DIR) == BuildStatus.DONE


def test_if_build_manager_is_waiting_for_finish_another_build(build_manager, mocked_builder, build_config, monkeypatch):
    _wait_for_build_to_finish = mock.MagicMock()
    monkeypatch.setattr(build_manager, '_wait_for_build_to_finish', _wait_for_build_to_finish)
    build_manager.update_status(BUILD_DIR, BuildStatus.IN_PROGRESS)

    build_manager.build(builder=mocked_builder, build_config=build_config)
    assert build_manager.get_status(BUILD_DIR) == BuildStatus.IN_PROGRESS
    _wait_for_build_to_finish.assert_called_once()


def test_if_test_is_failed_when_build_status_was_failed(build_manager, mocked_builder, build_config):
    build_manager.update_status(BUILD_DIR, BuildStatus.FAILED)

    expected_msg = f'Found in .*twister_builder.json the build status is set as {BuildStatus.FAILED} for: {BUILD_DIR}'
    with pytest.raises(TwisterBuildException, match=expected_msg):
        build_manager.build(builder=mocked_builder, build_config=build_config)


def test_if_build_manager_does_not_build_when_source_is_already_built(
        build_manager, mocked_builder, build_config, monkeypatch
):
    _wait_for_build_to_finish = mock.MagicMock()
    _build = mock.MagicMock()
    monkeypatch.setattr(build_manager, '_wait_for_build_to_finish', _wait_for_build_to_finish)
    monkeypatch.setattr(build_manager, '_build', _build)
    build_manager.update_status(BUILD_DIR, BuildStatus.DONE)

    build_manager.build(builder=mocked_builder, build_config=build_config)
    assert build_manager.get_status(BUILD_DIR) == BuildStatus.DONE
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
    build_manager.update_status(BUILD_DIR, BuildStatus.IN_PROGRESS)

    def update_status():
        time.sleep(0.1)
        build_manager.update_status(BUILD_DIR, BuildStatus.DONE)

    with run_job_in_thread(update_status):
        start_time = time.time()
        build_manager.build(builder=mocked_builder, build_config=build_config)
        finish_time = time.time()
    assert build_manager.get_status(BUILD_DIR) == BuildStatus.DONE
    assert finish_time - start_time < 2  # Should not wait longer than 1 second


def test_if_build_manager_waits_until_status_is_changed_to_failed(
        build_manager, mocked_builder, build_config
):
    build_manager.update_status(BUILD_DIR, BuildStatus.IN_PROGRESS)

    def update_status():
        time.sleep(0.1)
        build_manager.update_status(BUILD_DIR, BuildStatus.FAILED)

    expected_msg = f'Found in .*twister_builder.json the build status is set as ' \
                   f'{BuildStatus.FAILED} for: {BUILD_DIR}'
    with run_job_in_thread(update_status):
        with pytest.raises(TwisterBuildException, match=expected_msg):
            build_manager.build(builder=mocked_builder, build_config=build_config)
    assert build_manager.get_status(BUILD_DIR) == BuildStatus.FAILED


def test_if_build_manager_waits_until_timed_out(build_manager, mocked_builder, build_config):
    build_manager.update_status(BUILD_DIR, BuildStatus.IN_PROGRESS)
    build_manager.wait_build_timeout = 1
    expected_msg = f'Timed out waiting for another thread to finish building: {BUILD_DIR}'
    with pytest.raises(TwisterBuildException, match=expected_msg):
        build_manager.build(builder=mocked_builder, build_config=build_config)

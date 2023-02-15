import os
import subprocess
from unittest import mock
from unittest.mock import patch

import pytest

from twister2.device.qemu_adapter import QemuAdapter
from twister2.exceptions import TwisterException, TwisterRunException
from twister2.log_files.log_file import HandlerLogFile, NullLogFile


@pytest.fixture(name='device')
def fixture_device_adapter(tmp_path, twister_config) -> QemuAdapter:  # type: ignore[misc]
    build_dir = tmp_path / 'build_dir'
    adapter = QemuAdapter(twister_config, build_dir)
    yield adapter
    try:
        adapter.stop()  # to make sure all running processes are closed
    except TwisterException:
        pass


@patch('shutil.which', return_value='/usr/bin/west')
def test_if_generate_command_creates_proper_command(twister_config):
    adapter = QemuAdapter(twister_config, 'build_dir')
    adapter.generate_command('build_dir')
    assert adapter.command == ['/usr/bin/west', 'build', '-d', 'build_dir', '-t', 'run']


@patch('shutil.which', return_value=None)
def test_if_generate_command_creates_empty_listy_if_west_is_not_installed(twister_config):
    adapter = QemuAdapter(twister_config, 'build_dir')
    adapter.generate_command('build_dir')
    assert adapter.command == []


def test_if_qemu_adapter_raises_exception_for_empty_command(device) -> None:
    device.command = []
    exception_msg = 'Run simulation command is empty, please verify if it was generated properly.'
    with pytest.raises(TwisterRunException, match=exception_msg):
        device.flash_and_run(timeout=0.1)


def test_if_qemu_adapter_raises_exception_file_not_found(device) -> None:
    device.command = ['dummy']
    with pytest.raises(TwisterRunException, match='File not found: dummy'):
        device.flash_and_run(timeout=0.1)
        device.stop()
    assert device._exc is not None
    assert isinstance(device._exc, TwisterRunException)


@mock.patch('subprocess.Popen', side_effect=subprocess.SubprocessError(1, 'Exception message'))
def test_if_qemu_adapter_raises_exception_when_subprocess_raised_an_error(patched_run, device):
    device.command = ['echo', 'TEST']
    with pytest.raises(TwisterRunException, match='Exception message'):
        device.flash_and_run(timeout=0.1)
        device.stop()


def test_if_qemu_adapter_runs_without_errors(resources, twister_config, tmp_path) -> None:
    fifo_file_path = str(tmp_path / 'qemu-fifo')
    script_path = resources.joinpath('fifo_mock.py')
    device = QemuAdapter(twister_config, str(tmp_path))
    device.booting_timeout_in_ms = 1000
    device.command = ['python', str(script_path), fifo_file_path]
    device.connect()
    device.initialize_log_files(tmp_path)
    device.flash_and_run(timeout=1)
    lines = list(device.iter_stdout)
    assert 'Readability counts.' in lines
    assert os.path.isfile(device.handler_log_file.filename)
    with open(device.handler_log_file.filename, 'r') as file:
        file_lines = [line.strip() for line in file.readlines()]
    assert file_lines[0:2] == lines[0:2]
    device.disconnect()


def test_if_qemu_adapter_finishes_after_timeout(device) -> None:
    device.command = ['sleep', '0.3']
    device.flash_and_run(timeout=0.1)
    device.stop()
    assert device._process_ended_with_timeout is True


def test_handler_and_device_log_correct_initialized_on_qemu(device, tmp_path) -> None:
    device.initialize_log_files(tmp_path)
    assert isinstance(device.handler_log_file, HandlerLogFile)
    assert isinstance(device.device_log_file, NullLogFile)
    assert device.handler_log_file.filename.endswith('handler.log')  # type: ignore[union-attr]

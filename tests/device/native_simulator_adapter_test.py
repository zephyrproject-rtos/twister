import pytest

from twister2.device.native_simulator_adapter import NativeSimulatorAdapter
from twister2.exceptions import TwisterRunException
from twister2.twister_config import TwisterConfig


@pytest.fixture(name='device')
def fixture_adapter() -> NativeSimulatorAdapter:
    return NativeSimulatorAdapter(TwisterConfig('zephyr'))


def test_if_get_command_returns_proper_string(device, resources) -> None:
    command = device._get_command(resources)
    assert isinstance(command, list)
    assert command == [str(resources.joinpath('zephyr', 'zephyr.exe'))]


def test_if_native_simulator_adapter_runs_without_errors(monkeypatch, resources, device) -> None:
    """
    Run script which prints text line by line and ends without errors.
    Verify if subprocess was ended without errors, and without timeout.
    """
    script_path = resources.joinpath('mock_script.py')
    # patching original command by mock_script.py to simulate same behaviour as zephyr.exe
    monkeypatch.setattr(device, '_get_command', lambda _: ['python3', str(script_path)])
    device.run(build_dir='dummy', timeout=4)
    lines = list(device.iter_stdout)  # give it time before close thread
    device.stop()
    assert device._process_ended_with_timeout is False
    assert 'Readability counts.' in lines


def test_if_native_simulator_adapter_finishes_after_timeout(monkeypatch, device) -> None:
    monkeypatch.setattr(device, '_get_command', lambda _: ['sleep', '0.2'])
    device.run(build_dir='dummy', timeout=0.1)
    list(device.iter_stdout)
    device.stop()
    assert device._process_ended_with_timeout is True
    assert device._exc is None


def test_if_native_simulator_adapter_finishes_after_timeout_while_there_is_no_data_from_subprocess(
        monkeypatch, resources, device
) -> None:
    """Test if thread finishes after timeout when there is no data on stdout, but subprocess is still running"""
    script_path = resources.joinpath('mock_script.py')
    monkeypatch.setattr(device, '_get_command', lambda _: ['python3', str(script_path), '--long-sleep', '--sleep=5'])
    device.run(build_dir='dummy', timeout=0.5)
    lines = list(device.iter_stdout)
    device.stop()
    assert device._process_ended_with_timeout is True
    assert device._exc is None
    # this message should not be printed because script has been terminated due to timeout
    assert 'End of script' not in lines, 'Script has not been terminated before end'


def test_if_native_simulator_adapter_raises_exception_file_not_found(monkeypatch, device) -> None:
    monkeypatch.setattr(device, '_get_command', lambda _: ['dummy'])
    with pytest.raises(TwisterRunException, match='File not found: dummy'):
        device.run(build_dir='dummy', timeout=0.1)
        device.stop()
    assert device._exc is not None
    assert isinstance(device._exc, TwisterRunException)

import pytest

from twister2.device.native_simulator_adapter import NativeSimulatorAdapter
from twister2.exceptions import TwisterFlashException
from twister2.twister_config import TwisterConfig


@pytest.fixture(name='device')
def fixture_adapter() -> NativeSimulatorAdapter:
    return NativeSimulatorAdapter(TwisterConfig('zephyr'))


def test_if_get_command_returns_proper_string(device, resources) -> None:
    command = device._get_command(resources)
    assert isinstance(command, list)
    assert command == [str(resources.joinpath('zephyr', 'zephyr.exe'))]


def test_if_native_simulator_adapter_runs_without_errors(monkeypatch, resources, device) -> None:
    script_path = resources.joinpath('mock_script.py')
    monkeypatch.setattr(device, '_get_command', lambda _: ['python3', str(script_path)])
    device.flash('build', timeout=1)
    lines = list(device.out)
    device.stop()
    assert 'Readability counts.' in lines


def test_if_native_simulator_adapter_finishes_after_timeout(monkeypatch, resources, device) -> None:
    monkeypatch.setattr(device, '_get_command', lambda _: ['sleep', '0.2'])
    device.flash('build', timeout=0.1)
    list(device.out)  # give it time before close thread
    device.stop()
    assert device._process_ended_with_timeout is True
    assert device._exc is None


def test_if_native_simulator_adapter_finishes_after_timeout_2(monkeypatch, resources, device) -> None:
    """Test if thread finishes after timeout when there is no data on stdout but subprocess is still running"""
    script_path = resources.joinpath('mock_script.py')
    monkeypatch.setattr(device, '_get_command', lambda _: ['python3', str(script_path), '--long-sleep', '--sleep=5'])
    device.flash('build', timeout=1)
    list(device.out)
    device.disconnect()
    assert device._process_ended_with_timeout
    assert device._exc is None


def test_if_native_simulator_adapter_raises_exception_if_return_value_is_not_0(monkeypatch, resources, device) -> None:
    script_path = resources.joinpath('mock_script.py')
    monkeypatch.setattr(device, '_get_command', lambda _: ['python3', str(script_path), '--return-code=1'])
    with pytest.raises(TwisterFlashException, match='Flashing finished with errors for PID .*'):
        device.flash('build', timeout=0.5)
        device.stop()
        assert device._exc is not None


def test_if_native_simulator_adapter_raises_exception_file_not_found(monkeypatch, device) -> None:
    monkeypatch.setattr(device, '_get_command', lambda _: ['dummy'])
    with pytest.raises(TwisterFlashException, match='File not found: dummy'):
        device.flash('build', timeout=0.1)
        device.disconnect()
    assert device._exc is not None
    assert isinstance(device._exc, TwisterFlashException)


def test_if_native_simulator_adapter_raises_exception_subprocess_error(monkeypatch, resources, device) -> None:
    script_path = resources.joinpath('mock_script.py')
    monkeypatch.setattr(device, '_get_command', lambda _: ['python3', str(script_path), '--exception'])
    with pytest.raises(TwisterFlashException, match='Flashing finished with errors for PID .*'):
        device.flash('build', timeout=0.1)
        list(device.out)
        device.disconnect()
    assert device._exc is not None
    assert isinstance(device._exc, TwisterFlashException)

import pytest

from twister2.device.native_simulator_adapter import NativeSimulatorAdapter
from twister2.exceptions import TwisterRunException
from twister2.twister_config import TwisterConfig


@pytest.fixture(name='device')
def fixture_adapter() -> NativeSimulatorAdapter:
    return NativeSimulatorAdapter(TwisterConfig('zephyr'))


def test_if_get_command_returns_proper_string(device, resources) -> None:
    device.generate_command(resources)
    assert isinstance(device.command, list)
    assert device.command == [str(resources.joinpath('zephyr', 'zephyr.exe'))]


def test_if_native_simulator_adapter_runs_without_errors(resources, device) -> None:
    """
    Run script which prints text line by line and ends without errors.
    Verify if subprocess was ended without errors, and without timeout.
    """
    script_path = resources.joinpath('mock_script.py')
    # patching original command by mock_script.py to simulate same behaviour as zephyr.exe
    device.command = ['python3', str(script_path)]
    device.flash_and_run(timeout=4)
    lines = list(device.iter_stdout)  # give it time before close thread
    device.stop()
    assert device._process_ended_with_timeout is False
    assert 'Readability counts.' in lines


def test_if_native_simulator_adapter_finishes_after_timeout(device) -> None:
    device.command = ['sleep', '0.2']
    device.flash_and_run(timeout=0.1)
    list(device.iter_stdout)
    device.stop()
    assert device._process_ended_with_timeout is True
    assert device._exc is None


def test_if_native_simulator_adapter_finishes_after_timeout_while_there_is_no_data_from_subprocess(
        resources, device
) -> None:
    """Test if thread finishes after timeout when there is no data on stdout, but subprocess is still running"""
    script_path = resources.joinpath('mock_script.py')
    device.command = ['python3', str(script_path), '--long-sleep', '--sleep=5']
    device.flash_and_run(timeout=0.5)
    lines = list(device.iter_stdout)
    device.stop()
    assert device._process_ended_with_timeout is True
    assert device._exc is None
    # this message should not be printed because script has been terminated due to timeout
    assert 'End of script' not in lines, 'Script has not been terminated before end'


def test_if_native_simulator_adapter_raises_exception_file_not_found(device) -> None:
    device.command = ['dummy']
    with pytest.raises(TwisterRunException, match='File not found: dummy'):
        device.flash_and_run(timeout=0.1)
        device.stop()
    assert device._exc is not None
    assert isinstance(device._exc, TwisterRunException)


def test_if_simulator_adapter_raises_exception_empty_command(device) -> None:
    device.command = []
    exception_msg = 'Run simulation command is empty, please verify if it was generated properly.'
    with pytest.raises(TwisterRunException, match=exception_msg):
        device.flash_and_run(timeout=0.1)

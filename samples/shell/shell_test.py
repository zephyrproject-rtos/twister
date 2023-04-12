import time
import re
import pytest
import logging


logger = logging.getLogger(__name__)


def is_regex_found(regex, connection):
    """ A helper function telling if a given regex was found in an output"""
    pattern = re.compile(regex)
    matched = False
    timeout = 15  # [sec]
    time_end = time.time() + timeout
    while time.time() < time_end:
        line = connection.readline().decode('UTF-8').strip()
        logger.info(line)
        if pattern.match(line):
            matched = True
            break

    return matched


@pytest.mark.build_specification('sample.shell.shell_module')
def test_shell_help_and_ping(builder, dut):
    time.sleep(1)  # wait for application initialization on DUT
    dut.connection.write(b'help\n')
    assert is_regex_found('.*Please press the <Tab> button to see all available commands.*', dut.connection)
    dut.connection.write(b'demo ping\n')
    assert is_regex_found('.*pong*', dut.connection)


# This test uses the same configuration as the previous one so the building will be skipped
# This test will trigger another flashing of dut since it is using dut fixture which returns dut with flashed image
@pytest.mark.build_specification('sample.shell.shell_module')
def test_shell_introduce_self(builder, dut):
    time.sleep(1)  # wait for application initialization on DUT
    dut.connection.write(b'demo board\n')
    assert is_regex_found(builder.build_config.platform_name, dut.connection)

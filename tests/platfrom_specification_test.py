from twister2.platform_specification import PlatformSpecification


def test_load_platform_specification_from_yaml(resources):
    board_file = resources.joinpath('boards', 'arm', 'mps2_an521', 'mps2_an521_remote.yaml')
    platform = PlatformSpecification.load_from_yaml(board_file)
    assert isinstance(platform, PlatformSpecification)
    assert isinstance(platform.default, bool)
    assert isinstance(platform.ram, int)
    assert platform.ram == 4096
    assert platform.identifier == 'mps2_an521_remote'
    assert isinstance(platform.toolchain, list)
    assert isinstance(platform.supported, set)
    assert platform.supported == {'clock_controller', 'eeprom', 'gpio', 'i2c', 'pinmux', 'serial'}

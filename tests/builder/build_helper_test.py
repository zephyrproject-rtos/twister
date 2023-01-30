from __future__ import annotations

from pathlib import Path

import pytest

from twister2.builder.build_helper import CMakeExtraArgsConfig, CMakeExtraArgsGenerator

WARNING_AS_ERROR_ARGS: list[str] = [
    '-DEXTRA_CFLAGS=-Werror',
    '-DEXTRA_AFLAGS=-Werror -Wa,--fatal-warnings',
    '-DEXTRA_LDFLAGS=-Wl,--fatal-warnings',
    '-DEXTRA_GEN_DEFINES_ARGS=--edtlib-Werror'
]


@pytest.fixture
def args_config(tmp_path) -> CMakeExtraArgsConfig:
    """Return CMakeExtraArgsConfig"""
    return CMakeExtraArgsConfig(
        run_id='df5eab0fcd4a72cdc4804bc04135e3d7',
        build_dir=tmp_path,
        device_type='hardware',
        fifo_file=Path('fifo_file'),
        platform_arch='arm',
        platform_name='frdm_k64f',
        extra_args_spec=[],
        extra_configs=[],
        extra_args_cli=[],
    )


@pytest.fixture
def args_generator(args_config) -> CMakeExtraArgsGenerator:
    """Return CMakeExtraArgsGenerator"""
    return CMakeExtraArgsGenerator(args_config)


def test_if_cmake_args_generator_produce_correct_basic_args(
        args_config: CMakeExtraArgsConfig, args_generator: CMakeExtraArgsGenerator
):
    cmake_extra_args = args_generator.generate()
    assert cmake_extra_args == [f'-DTC_RUNID={args_config.run_id}'] + WARNING_AS_ERROR_ARGS


def test_if_cmake_args_generator_produce_correct_qemu_arg(
        args_config: CMakeExtraArgsConfig, args_generator: CMakeExtraArgsGenerator
):
    args_config.device_type = 'qemu'
    args_generator.config = args_config
    cmake_extra_args = args_generator.generate()
    assert f'-DQEMU_PIPE={args_config.fifo_file}' in cmake_extra_args


def test_if_cmake_args_generator_parse_extra_configs_correctly(
        args_config: CMakeExtraArgsConfig, args_generator: CMakeExtraArgsGenerator
):
    args_config.extra_configs = [
        f'arch:{args_config.platform_arch}:CONFIG_A=y',
        'arch:dummy_arch:CONFIG_B=y',
        f'platform:{args_config.platform_name}:CONFIG_C=y',
        'platform:dummy_platform:CONFIG_D=y',
        'CONFIG_E=y'
    ]
    args_generator.config = args_config
    parsed_extra_configs = args_generator._parse_extra_configs()
    expected = ['CONFIG_A=y', 'CONFIG_C=y', 'CONFIG_E=y']
    assert parsed_extra_configs == expected


def test_if_cmake_args_generator_export_extra_configs_correctly(
        args_config: CMakeExtraArgsConfig, args_generator: CMakeExtraArgsGenerator
):
    extra_configs = ['CONFIG_BOOT_BANNER=n', 'CONFIG_BOOT_DELAY=600']
    args_config.extra_configs = extra_configs
    args_generator.config = args_config
    extra_args = args_generator._prepare_extra_configs()
    expected_overlay_config_file_path = args_config.build_dir / 'twister' / 'testsuite_extra.conf'
    expected_extra_args = [f'OVERLAY_CONFIG="{expected_overlay_config_file_path}"']
    assert extra_args == expected_extra_args
    with open(expected_overlay_config_file_path, 'r') as file:
        extra_configs_from_file = [item.strip() for item in file.readlines()]
        assert extra_configs_from_file == extra_configs


def test_if_cmake_args_generator_prepare_extra_args_spec_correctly(
        args_config: CMakeExtraArgsConfig, args_generator: CMakeExtraArgsGenerator
):
    extra_args_spec = [
        'CONF_FILE="prj_single.conf"',
        'OVERLAY_CONFIG="prj_single_overlay.conf"',
        'OVERLAY_CONFIG="twister/testsuite_extra.conf"',
    ]
    cmake_args = args_generator._prepare_extra_args_spec(extra_args_spec)
    expected_cmake_args = [
        '-DCONF_FILE=prj_single.conf',
        '-DOVERLAY_CONFIG=prj_single_overlay.conf twister/testsuite_extra.conf'
    ]
    assert cmake_args == expected_cmake_args


def test_if_cmake_args_generator_prepare_extra_args_cli_correctly(
        args_config: CMakeExtraArgsConfig, args_generator: CMakeExtraArgsGenerator
):
    extra_args_cli = ['CONF_FILE="prj_single.conf"']
    cmake_args = args_generator._prepare_extra_args_cli(extra_args_cli)
    expected_cmake_args = ['-DCONF_FILE=\"prj_single.conf\"']
    assert cmake_args == expected_cmake_args

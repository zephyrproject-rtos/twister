import subprocess
from unittest import mock

import pytest

from twister2.exceptions import TwisterBuildException


@pytest.fixture
def patched_cmake():
    with mock.patch('twister2.builder.cmake_builder.CmakeBuilder._get_cmake', return_value='cmake') as cmake:
        yield cmake


@mock.patch('twister2.builder.cmake_builder.CmakeBuilder.run_cmake', return_value=None)
@mock.patch('twister2.builder.cmake_builder.CmakeBuilder.run_build_generator', return_value=None)
def test_if_run_build_generator_is_not_called_when_cmake_helper_is_selected(
        run_build_generator, run_cmake, cmake_builder
):
    cmake_builder.build(cmake_helper=True)
    run_cmake.assert_called_once_with(True)
    run_build_generator.assert_not_called()


@mock.patch('twister2.builder.cmake_builder.CmakeBuilder.run_cmake', return_value=None)
@mock.patch('twister2.builder.cmake_builder.CmakeBuilder.run_build_generator', return_value=None)
def test_if_run_build_generator_is_called_when_cmake_helper_is_not_selected(
        run_build_generator, run_cmake, cmake_builder
):
    cmake_builder.build(cmake_helper=False)
    run_cmake.assert_called_once_with(False)
    run_build_generator.assert_called_once()


@mock.patch('twister2.builder.cmake_builder.CmakeBuilder._run_command_in_subprocess', return_value=None)
def test_if_run_cmake_calls_run_command_in_subprocess_with_proper_arguments(
        patched_run_command_in_subprocess, patched_cmake, cmake_builder, build_config
):
    expected_command = [
        'cmake', f'-S{build_config.source_dir}', f'-B{build_config.build_dir}',
        f'-DBOARD={build_config.platform_name}', '-DEXTRA_CFLAGS=-Werror',
        '-DEXTRA_AFLAGS=-Werror -Wa,--fatal-warnings', '-DEXTRA_LDFLAGS=-Wl,--fatal-warnings',
        '-DEXTRA_GEN_DEFINES_ARGS=--edtlib-Werror', '-DCONF_FILE=prj_single.conf',
    ]

    cmake_builder.run_cmake(cmake_helper=False)
    patched_run_command_in_subprocess.assert_called_once_with(expected_command, action='Cmake')


@mock.patch('twister2.builder.cmake_builder.CmakeBuilder._run_command_in_subprocess', return_value=None)
def test_if_run_cmake_calls_run_command_in_subprocess_with_proper_arguments_for_cmake_helper_flag_set(
        patched_run_command_in_subprocess, patched_cmake, cmake_builder, build_config
):
    expected_command = [
        'cmake', f'-S{build_config.source_dir}', f'-B{build_config.build_dir}',
        f'-DBOARD={build_config.platform_name}', '-DEXTRA_CFLAGS=-Werror',
        '-DEXTRA_AFLAGS=-Werror -Wa,--fatal-warnings', '-DEXTRA_LDFLAGS=-Wl,--fatal-warnings',
        '-DEXTRA_GEN_DEFINES_ARGS=--edtlib-Werror', '-DCONF_FILE=prj_single.conf',
        '-DMODULES=dts,kconfig', '-Pzephyr/cmake/package_helper.cmake'
    ]

    cmake_builder.run_cmake(cmake_helper=True)
    patched_run_command_in_subprocess.assert_called_once_with(expected_command, action='Cmake')


@mock.patch('twister2.builder.cmake_builder.CmakeBuilder._run_command_in_subprocess', return_value=None)
def test_if_run_build_generator_calls_run_command_with_proper_arguments(
        patched_run_command_in_subprocess, patched_cmake, cmake_builder, build_config
):
    expected_command = ['cmake', '--build', build_config.build_dir]

    cmake_builder.run_build_generator()
    patched_run_command_in_subprocess.assert_called_once_with(expected_command, action='building')


@mock.patch('shutil.which', return_value='cmake')
def test_if_get_cmake_returns_path_to_installed_cmake(patched_which, cmake_builder):
    assert cmake_builder._get_cmake() == 'cmake'


@mock.patch('shutil.which', return_value=None)
def test_if_get_cmake_raises_exception_when_cmake_is_not_installed(patched_which, cmake_builder):
    with pytest.raises(TwisterBuildException, match='cmake not found'):
        cmake_builder._get_cmake()


@mock.patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'error message'))
def test_if_run_command_in_subprocess_handles_subprocess_process_error(patched_run, cmake_builder):
    with pytest.raises(TwisterBuildException, match='CMake error'):
        cmake_builder._run_command_in_subprocess(['dummie'], 'building')


@mock.patch('subprocess.run')
def test_if_run_command_in_subprocess_handles_subprocess_return_code_zero_without_errors(
        patched_run, cmake_builder
):
    patched_run.return_value = mock.MagicMock(returncode=0)
    cmake_builder._run_command_in_subprocess(['dummie'], 'building')


@mock.patch('subprocess.run')
def test_if_run_command_in_subprocess_handles_subprocess_non_zero_return_code(patched_run, cmake_builder):
    patched_run.return_value = mock.MagicMock(returncode=1)
    msg = (
        f'Failed running CMake {cmake_builder.build_config.source_dir} '
        f'for platform: {cmake_builder.build_config.platform_name}'
    )
    with pytest.raises(TwisterBuildException, match=msg):
        cmake_builder._run_command_in_subprocess(['dummie'], 'building')

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from twister2.exceptions import TwisterException
from twister2.helper import log_command

logger = logging.getLogger(__name__)


def get_toolchain_version(output_dir: str, zephyr_base: str) -> str:
    """
    When TwisterConfig is generated first time, then information about used
    toolchain version should be taken by CMake script and then saved into
    environment_info.json file. In case when xdist is used, then every time when
    TwisterConfig is generated once again by each worker, information about used
    toolchain version can be taken from environment_info.json file to avoid
    calling CMake script several times in row.
    """
    environment_info_file_name = 'environment_info.json'
    environment_info_file_path: Path = Path(output_dir) / environment_info_file_name

    if environment_info_file_path.is_file():
        used_toolchain_version = _get_toolchain_version_from_env_info_file(environment_info_file_path)
    else:
        used_toolchain_version = _get_toolchain_version_from_cmake_script(zephyr_base)
        _save_toolchain_version_to_env_info_file(environment_info_file_path, used_toolchain_version)

    return used_toolchain_version


def _get_toolchain_version_from_env_info_file(file_path: Path) -> str:
    try:
        with open(file_path, 'r') as file:
            environment_info = json.load(file)
            used_toolchain_version = environment_info['used_toolchain_version']
    except Exception:
        logger.error('Problem with get info about used toolchain version.')
        raise
    return used_toolchain_version


def _save_toolchain_version_to_env_info_file(file_path: Path, toolchain_version: str) -> None:
    environment_info = {'used_toolchain_version': toolchain_version}
    with open(file_path, 'w') as file:
        json.dump(environment_info, file, indent=4)


def _get_toolchain_version_from_cmake_script(zephyr_base: str) -> str:
    """
    TODO: this function was copied from Twister v1 and requires some refactoring in the future
    TODO: write unit tests dedicated for this function
    """
    toolchain_script = Path(zephyr_base) / 'cmake' / 'verify-toolchain.cmake'
    result = _run_cmake_script(toolchain_script, ['FORMAT=json'])

    try:
        if result.get('returncode') != 0:
            logger.error(result['returnmsg'])
            pytest.exit(result['returnmsg'], returncode=2)
    except KeyError:
        msg = 'Problem with get toolchain version by CMake script.'
        logger.error(msg)
        pytest.exit(msg, returncode=2)

    toolchain_version = json.loads(result['stdout'])['ZEPHYR_TOOLCHAIN_VARIANT']
    logger.info(f"Using '{toolchain_version}' toolchain.")
    return toolchain_version


def _run_cmake_script(script: str | Path, cmake_extra_args: list[str] | None = None) -> dict:
    """
    TODO: this function was copied from Twister v1 and requires some refactoring in the future
    TODO: write unit tests dedicated for this function
    """
    if cmake_extra_args is None:
        cmake_extra_args = []

    script = os.fspath(script)

    logger.debug('Running cmake script %s', script)

    cmake_args = ['-D{}'.format(a.replace('"', '')) for a in cmake_extra_args]
    cmake_args.extend(['-P', script])

    if (cmake := shutil.which('cmake')) is None:
        raise TwisterException('cmake not found')

    cmd = [cmake] + cmake_args
    log_command(logger, 'Calling cmake', cmd)

    # CMake sends the output of message() to stderr unless it's STATUS
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    process_output, _ = p.communicate()

    # It might happen that the environment adds ANSI escape codes like \x1b[0m,
    # for instance if twister is executed from inside a makefile. In such a
    # scenario it is then necessary to remove them, as otherwise the JSON decoding
    # will fail.
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    out = ansi_escape.sub('', process_output.decode())

    if p.returncode == 0:
        msg = f'Finished running {script}'
        logger.debug(msg)
        results = {'returncode': p.returncode, 'msg': msg, 'stdout': out}

    else:
        logger.error('Cmake script failure: %s' % script)
        results = {'returncode': p.returncode, 'returnmsg': out}

    return results

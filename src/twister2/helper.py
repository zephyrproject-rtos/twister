from __future__ import annotations

import logging
import os.path
import platform
import shlex
from pathlib import Path

import yaml.parser

from twister2.exceptions import TwisterException

_WINDOWS = (platform.system() == 'Windows')

logger = logging.getLogger(__name__)


def string_to_set(value: str | set) -> set[str]:
    if isinstance(value, str):
        return set(value.split())
    else:
        return value


def string_to_list(value: str | list) -> list[str]:
    if isinstance(value, str):
        return list(value.split())
    else:
        return value


def safe_load_yaml(filename: Path) -> dict:
    """
    Return data from yaml file.

    :param filename: path to yaml file
    :return: data read from yaml file
    """
    __tracebackhide__ = True
    with filename.open(encoding='UTF-8') as file:
        try:
            data = yaml.safe_load(file)
        except yaml.parser.ParserError as exc:
            logger.error('Parsing error for yaml file %s: %s', filename, exc)
            raise TwisterException(f'Cannot load data from yaml file: {filename}')
        else:
            return data


def log_command(logger: logging.Logger, msg: str, args: list, level: int = logging.DEBUG):
    """
    Platform-independent helper for logging subprocess invocations.

    Will log a command string that can be copy/pasted into a POSIX
    shell on POSIX platforms. This is not available on Windows, so
    the entire args array is logged instead.

    :param logger: logging.Logger to use
    :param msg: message to associate with the command
    :param args: argument list as passed to subprocess module
    :param level: log level
    """
    msg = f'{msg}: %s'
    if _WINDOWS:
        logger.log(level, msg, str(args))
    else:
        logger.log(level, msg, shlex.join(args))


def normalize_filename(filename: str) -> str:
    filename = os.path.expanduser(os.path.expandvars(filename))
    filename = os.path.normpath(os.path.abspath(filename))
    return filename

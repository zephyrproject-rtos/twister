from __future__ import annotations

import logging

import pytest


def configure_logging(config: pytest.Config) -> None:
    log_file = 'twister2.log'
    if hasattr(config, 'workerinput'):
        worker_id = config.workerinput['workerid']
        log_file = f'twister2_{worker_id}.log'
    log_level = config.getoption('--log-level') or logging.INFO
    log_file = config.getoption('--log-file') or log_file
    logging.basicConfig(
        level=log_level,
        filename=log_file,
        filemode='w',
        format='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
    )


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

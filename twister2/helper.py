import logging

import pytest

from twister2.yaml_test_function import YamlTestFunction


def is_yaml_test(item: pytest.Item) -> bool:
    """Return True if item is a yaml test."""
    if isinstance(item, YamlTestFunction):
        return True
    else:
        return False


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

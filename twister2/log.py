from __future__ import annotations

import logging.config
import os

import pytest


def configure_logging(config: pytest.Config) -> None:
    output_dir = config.getoption('--outdir')
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, 'twister2.log')
    testcases_file = os.path.join(output_dir, 'testcases_creation.log')

    if hasattr(config, 'workerinput'):
        worker_id = config.workerinput['workerid']
        log_file = os.path.join(output_dir, f'twister2_{worker_id}.log')

    log_format = '%(asctime)s:%(levelname)s:%(name)s: %(message)s'
    log_level = config.getoption('--log-level') or logging.INFO
    log_file = config.getoption('--log-file') or log_file

    default_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format,
            },
            'simply': {
                'format': '%(message)s'
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filters': [],
                'filename': log_file,
                'encoding': 'utf8',
                'mode': 'w'
            },
            'file_with_skipped_tests': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'simply',
                'filters': [],
                'filename': testcases_file,
                'encoding': 'utf8',
                'mode': 'w'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filters': [],
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',
                'propagate': False
            },
            'twister2': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False,
            },
            'testcases': {  # logger to log tests which are skipped on tests collection phase
                'handlers': ['file_with_skipped_tests'],
                'level': 'DEBUG',
                'propagate': False
            }
        }
    }

    logging.config.dictConfig(default_config)

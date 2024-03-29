import logging
import os

import pytest

from twister2.log_files.log_file import LogFile

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_log_file(tmpdir):
    log_file = LogFile.create(build_dir=tmpdir)
    yield log_file


def test_if_filename_is_correct(sample_log_file):
    assert sample_log_file.filename.endswith('uninitialized.log')


def test_handle_data_is_str(sample_log_file):
    msg = 'str message'
    sample_log_file.handle(data=msg)
    assert os.path.exists(path=sample_log_file.filename)
    with open(file=sample_log_file.filename, mode='r') as file:
        assert file.readline() == 'str message'


def test_handle_data_is_byte(sample_log_file):
    msg = b'bytes message'
    sample_log_file.handle(data=msg)
    assert os.path.exists(path=sample_log_file.filename)
    with open(file=sample_log_file.filename, mode='r') as file:
        assert file.readline() == 'bytes message'


def test_handle_data_is_none(sample_log_file):
    msg = None
    sample_log_file.handle(data=msg)
    assert not os.path.exists(path=sample_log_file.filename)


def test_get_log_filename_null_filename():
    log_file = LogFile.create()
    assert log_file.filename == os.devnull


def test_get_log_filename_sample_filename(tmpdir):
    log_file = LogFile.create(build_dir=tmpdir)
    assert log_file.filename == os.path.join(tmpdir, 'uninitialized.log')

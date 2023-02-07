import logging
import os
import pytest

from twister2.log_file.build_log_file import BuildLogFile

logger = logging.getLogger(__name__)


@pytest.fixture
def build_log(tmpdir) -> BuildLogFile:
    build_log = BuildLogFile(build_dir=tmpdir)
    yield build_log


def test_if_filename_is_correct(build_log):
    assert build_log.filename.endswith('build.log')


def test_handle_data_is_str(build_log):
    msg = 'str message'
    build_log.handle(data=msg)
    assert os.path.exists(path=build_log.filename)
    with open(file=build_log.filename, mode='r') as file:
        assert file.readline() == 'str message'


def test_handle_data_is_byte(build_log):
    msg = b'bytes message'
    build_log.handle(data=msg)
    assert os.path.exists(path=build_log.filename)
    with open(file=build_log.filename, mode='r') as file:
        assert file.readline() == 'bytes message'


def test_handle_data_is_none(build_log):
    msg = None
    build_log.handle(data=msg)
    assert not os.path.exists(path=build_log.filename)

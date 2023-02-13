from collections import namedtuple
from pathlib import Path
from unittest import mock

import pytest

from twister2.platform_specification import PlatformSpecification
from twister2.twister_config import TwisterConfig

pytest_plugins = ['pytester']


@pytest.fixture
def resources(request: pytest.FixtureRequest) -> Path:
    """Return path to `data` folder"""
    return Path(request.module.__file__).parent.joinpath('data')


@pytest.fixture(scope='function')
def platform() -> PlatformSpecification:
    """Return instance of PlatformSpecification"""
    return PlatformSpecification(identifier='platform_xyz')


@pytest.fixture(scope='function')
def twister_config(platform) -> TwisterConfig:
    """Return new instance of TwisterConfig"""
    return TwisterConfig(
        zephyr_base='dummy_path',
        selected_platforms=[platform.identifier],
        platforms=[platform]
    )


@pytest.fixture(scope='function')
def copy_example(pytester) -> Path:
    """Copy example tests to temporary directory and return path the temp directory."""
    resources_dir = Path(__file__).parent / 'data'
    pytester.copy_example(str(resources_dir))
    return pytester.path


@pytest.fixture(scope='function', autouse=True)
def mock_get_toolchain_version():
    """
    we need to mock
    twister2.environment.environment._get_toolchain_version_from_cmake_script
    because in unit tests we don't have Zephyr repo to call this script
    """
    with mock.patch('twister2.environment.environment._get_toolchain_version_from_cmake_script') as mocked_object:
        mocked_object.return_value = 'zephyr'
        yield mocked_object


@pytest.fixture(scope='function', autouse=True)
def mock_get_zephyr_repo_info():
    """
    we need to mock
    twister2.environment.environment.get_zephyr_repo_info
    because in unit tests we don't have Zephyr repo to call this script
    """
    with mock.patch('twister2.environment.environment.get_zephyr_repo_info') as mocked_object:
        RepoInfo = namedtuple('RepoInfo', 'zephyr_version commit_date')
        mocked_object.return_value = RepoInfo('123456789012', '20220102')
        yield mocked_object

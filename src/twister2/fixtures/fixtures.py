import pytest

from twister2.fixtures.common import SetupTestManager


@pytest.fixture(name='setup_manager', scope='function')
def fixture_setup_manager(request: pytest.FixtureRequest) -> SetupTestManager:
    """Test setup manager"""
    return SetupTestManager(request)

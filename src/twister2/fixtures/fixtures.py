from twister2.fixtures.common import TestSetupManager

import pytest


@pytest.fixture(name='setup_manager', scope='function')
def fixture_setup_manager(request: pytest.FixtureRequest) -> TestSetupManager:
    """Test setup manager"""
    return TestSetupManager(request)

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parents[1]))

pytest_plugins = ['pytester']


@pytest.fixture
def resources(request: pytest.FixtureRequest) -> Path:
    """Return path to `data` folder"""
    return Path(request.module.__file__).parent.joinpath('data')

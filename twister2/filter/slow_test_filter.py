from __future__ import annotations

import pytest

from twister2.filter.filter_interface import FilterInterface


class SlowTestFilter(FilterInterface):
    """Filter slow tests."""

    def __init__(self, config: pytest.Config):
        super().__init__(config)
        self.enable_slow = config.getoption('--enable-slow')

    def filter(self, item: pytest.Item) -> bool:
        if item.get_closest_marker('slow') and not self.enable_slow:
            return True
        return False

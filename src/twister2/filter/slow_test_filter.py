from __future__ import annotations

import pytest

from twister2.filter.filter_interface import FilterInterface


class SlowTestFilter(FilterInterface):
    """Filter slow tests."""

    def __init__(self, config: pytest.Config) -> None:
        """
        :param config: pytest configuration
        """
        super().__init__(config)
        self.enable_slow = config.getoption('--enable-slow')

    def filter(self, item: pytest.Item) -> bool:
        """
        Check if test should be deselected

        :param item: pytest test item
        :return: True if test should be deselected
        """
        if item.get_closest_marker('slow') and not self.enable_slow:
            return True
        return False

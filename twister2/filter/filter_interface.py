from __future__ import annotations

import abc

import pytest


class FilterInterface(abc.ABC):
    """Filter tests by tag."""

    def __init__(self, config: pytest.Config):
        self.config = config

    def filter(self, item: pytest.Item) -> bool:
        """Return true if item should be deselected."""

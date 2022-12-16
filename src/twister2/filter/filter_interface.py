from __future__ import annotations

import abc

import pytest


class FilterInterface(abc.ABC):
    """Filter interface."""

    def __init__(self, config: pytest.Config):
        self.config = config

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    @abc.abstractmethod
    def filter(self, item: pytest.Item) -> bool:
        """Return true if item should be deselected."""

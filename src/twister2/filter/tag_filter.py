from __future__ import annotations

from typing import List, Sequence, Set

import pytest

from twister2.filter.filter_interface import FilterInterface


class TagFilter(FilterInterface):
    """Filter tests by tag."""

    def __init__(self, config: pytest.Config):
        super().__init__(config)
        self.user_tags: list[str] = config.getoption('tags') or []
        self.tag_matcher: TagMatcher = TagMatcher(self.user_tags)

    def filter(self, item: pytest.Item) -> bool:
        """
        Check if test should be deselected.

        :param item: pytest test item
        :return: True if test should be deselected
        """
        if self.user_tags:
            item_tags: set[str] = self.get_item_tags(item)
            return not self.tag_matcher.should_run_with(item_tags)
        else:
            return False

    @staticmethod
    def get_item_tags(item: pytest.Item) -> Set[str]:
        """Return tags assigned to test item."""
        tags: set[str] = set()
        for marker in item.iter_markers(name='tags'):
            tags.update(marker.args)
        return tags


class TagMatcher:
    """Check if test item should be run or not."""

    def __init__(self, tags: Sequence[str] | None = None) -> None:
        """
        :param tags: list of tags selected by user
        """
        self.selected: List[Set[str]] = []  #: store selected tags
        self.deselected: List[Set[str]] = []  #: store deselected tags
        if tags is None:
            tags = []
        self.parse(tags)

    def parse(self, item_tags: Sequence[str]) -> None:
        """
        :param item_tags: test tags separated by comma
        """
        for tags in item_tags:
            include_tags = set()
            exclude_tags = set()
            for tag in (t.replace('@', '') for t in tags.split(',')):
                if tag.startswith('~'):
                    exclude_tags.add(tag[1:])
                else:
                    include_tags.add(tag)
            if include_tags:
                self.selected.append(include_tags)
            if exclude_tags:
                self.deselected.append(exclude_tags)

    def should_run_with(self, tags: Set[str]) -> bool:
        """
        :param tags: tags assigned to test
        :return: True if test should be executed
        """
        results = []
        tags = set(tags)
        for selected_tags in self.selected:
            results.append(self._should_be_selected(tags, selected_tags))
        for deselected_tags in self.deselected:
            results.append(not self._should_be_deselected(tags, deselected_tags))
        return all(results)

    @staticmethod
    def _should_be_deselected(tags1: set, tags2: set) -> bool:
        return bool(tags1 & tags2)

    @staticmethod
    def _should_be_selected(tags1: set, tags2: set) -> bool:
        return bool(tags1 & tags2)

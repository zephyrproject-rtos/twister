"""
Module contains helper function used in report package.
"""
from __future__ import annotations

import pytest


def get_suite_name(item: pytest.Item) -> str:
    """Return suite name."""
    if hasattr(item, 'cls') and item.cls:
        return f'{item.module.__name__}::{item.cls.__name__}'  # type: ignore[attr-defined]
    elif hasattr(item, 'module') and hasattr(item.module, '__name__'):
        return f'{item.module.__name__}'
    else:
        return item.parent.nodeid.replace('/', '.').replace('\\', '.')  # type: ignore[union-attr]


def get_test_name(item: pytest.Item) -> str:
    """Return test name."""
    return item.name


def get_test_path(item: pytest.Item) -> str:
    """Return path to file where test is defined."""
    return item.parent.nodeid  # type: ignore[union-attr]


def get_item_type(item: pytest.Item) -> str:
    """Return test type."""
    if marker := item.get_closest_marker('type'):
        return marker.args[0]
    return ''


def get_item_quarantine(item: pytest.Item) -> str:
    """Return quarantine reason if test should be under quarantine."""
    if marker := item.get_closest_marker('quarantine'):
        return marker.args[0] if marker.args else 'unknown reason'
    return ''


def get_item_platform(item: pytest.Item) -> str:
    """Return test platform."""
    if marker := item.get_closest_marker('platform'):
        return marker.args[0]
    return ''


def get_item_platform_allow(item: pytest.Item) -> str:
    """Return allowed platforms."""
    if hasattr(item.session, 'specification'):
        if spec := item.session.specification.get(item.nodeid):
            return ' '.join(spec.platform_allow)
    return ''


def get_item_runnable_status(item: pytest.Item) -> bool:
    """Return runnable status."""
    if hasattr(item.session, 'specification'):
        if spec := item.session.specification.get(item.nodeid):
            return spec.runnable
    return True


def get_item_tags(item: pytest.Item) -> str:
    """Return comma separated tags."""
    if marker := item.get_closest_marker('tags'):
        tags: list[str] = list(marker.args)
    else:
        tags = []
    return ' '.join(tags)


def get_item_build_only_status(item: pytest.Item) -> bool:
    """Return True if test is build_only"""
    if item.get_closest_marker('build_only'):
        return True
    return False

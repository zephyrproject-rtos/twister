"""
Module contains helper function used in report package.
"""
import pytest

from twister2.yaml_test_function import YamlTestFunction


def get_suite_name(item: pytest.Item) -> str:
    """Return suite name."""
    if hasattr(item, 'cls') and item.cls:
        return f'{item.module.__name__}::{item.cls.__name__}'
    elif hasattr(item, 'module') and hasattr(item.module, '__name__'):
        return f'{item.module.__name__}'
    else:
        return item.parent.nodeid.replace('/', '.').replace('\\', '.')


def get_test_name(item: pytest.Item) -> str:
    """Return test name."""
    return item.name


def get_test_path(item: pytest.Item) -> str:
    """Return path to file where test is defined."""
    return item.parent.nodeid


def get_item_type(item: pytest.Item) -> str:
    """Return test type."""
    if marker := item.get_closest_marker('type'):
        return marker.args[0]
    return ''


def get_item_skip(item: pytest.Item) -> str:
    """Return skip reason if test should be skipped."""
    if marker := item.get_closest_marker('skip'):
        return marker.args[0]
    return None


def get_item_platform(item: pytest.Item) -> str:
    """Return test platform."""
    if marker := item.get_closest_marker('platform'):
        return marker.args[0]
    return ''


def get_item_platform_allow(item: pytest.Item) -> str:
    """Return allowed platforms."""
    if isinstance(item, YamlTestFunction):
        return ' '.join(item.function.spec.platform_allow)
    return ''


def get_item_tags(item: pytest.Item) -> str:
    """Return comma separated tags."""
    if marker := item.get_closest_marker('tags'):
        tags = marker.args
    else:
        tags = []
    return ' '.join(tags)

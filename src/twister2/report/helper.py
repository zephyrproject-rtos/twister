"""
Module contains helper function used in report package.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


def get_suite_name(item: pytest.Item) -> str:
    """Return suite name."""
    if hasattr(item, 'cls') and item.cls:
        return f'{item.module.__name__}::{item.cls.__name__}'  # type: ignore[attr-defined]
    elif hasattr(item, 'module') and hasattr(item.module, '__name__'):
        return f'{item.module.__name__}'
    else:
        # TODO: Below is a copy of workflow used in TestSuite.get_unique() from V1 to achieve name parity.

        # Use this for internal comparisons; that's what canonicalization is
        # for. Don't use it when invoking other components of the build system
        # to avoid confusing and hard to trace inconsistencies in error messages
        # and logs, generated Makefiles, etc. compared to when users invoke these
        # components directly.
        # Note "normalization" is different from canonicalization, see os.path.
        canonical_zephyr_base = os.path.realpath(item.config.twister_config.zephyr_base)
        suite_root = os.path.abspath(item.path.parent)
        suite_path = os.path.dirname(item.path)
        workdir = os.path.relpath(suite_path, suite_root)
        name = item.originalname
        return get_suite_name_v1_style(suite_root, workdir, name, canonical_zephyr_base)  # type: ignore[union-attr]


def get_suite_name_v1_style(testsuite_root, workdir, name, canonical_zephyr_base) -> str:
    """Return exact same name as in V1. Copy 1:1 of V1 TestSuite.get_unique()"""

    canonical_testsuite_root = os.path.realpath(testsuite_root)
    if Path(canonical_zephyr_base) in Path(canonical_testsuite_root).parents:
        # This is in ZEPHYR_BASE, so include path in name for uniqueness
        relative_ts_root = os.path.relpath(canonical_testsuite_root, start=canonical_zephyr_base)
    else:
        relative_ts_root = ''

    # workdir can be "."
    unique = os.path.normpath(os.path.join(relative_ts_root, workdir, name))
    check = name.split('.')
    if len(check) < 2:
        raise Exception(f"""bad test name '{name}' in {testsuite_root}/{workdir}. \
Tests should reference the category and subsystem with a dot as a separator.
                """
                        )
    return unique


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


def get_item_platform(item: pytest.Item) -> str:
    """Return test platform."""
    if marker := item.get_closest_marker('platform'):
        return marker.args[0]
    return ''


def get_item_arch(item: pytest.Item) -> str:
    """Return test platform arch."""
    platform_name = get_item_platform(item)
    if platform_name:
        platform_obj = item.config.twister_config.get_platform(platform_name)
        return platform_obj.arch
    return ''


def get_run_id(item: pytest.Item) -> str:
    """Return run id."""
    if hasattr(item.session, 'specifications'):
        if spec := item.session.specifications.get(item.nodeid):
            return spec.run_id
    return ''


def get_retries(item: pytest.Item) -> int:
    """Return `retries` from specification."""
    if hasattr(item.session, 'specifications'):
        if spec := item.session.specifications.get(item.nodeid):
            return spec.retries
    return 0


def get_item_platform_allow(item: pytest.Item) -> str:
    """Return allowed platforms."""
    if hasattr(item.session, 'specifications'):
        if spec := item.session.specifications.get(item.nodeid):
            return ' '.join(spec.platform_allow)
    return ''


def get_item_runnable_status(item: pytest.Item) -> bool:
    """Return runnable status."""
    if hasattr(item.session, 'specifications'):
        if spec := item.session.specifications.get(item.nodeid):
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

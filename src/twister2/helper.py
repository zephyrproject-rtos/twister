from __future__ import annotations


def string_to_set(value: str | set) -> set[str]:
    if isinstance(value, str):
        return set(value.split())
    else:
        return value


def string_to_list(value: str | list) -> list[str]:
    if isinstance(value, str):
        return list(value.split())
    else:
        return value

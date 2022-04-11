from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class YamlTestSpecification:
    """Test specification for yaml test."""
    name: str  #: test case name plus platform
    original_name: str  #: keeps test case name without platform
    path: Path  #: path to a folder where C files are stored
    platform: str  #: platform name used for this test
    tags: set = field(default_factory=set)
    type: str = 'integration'
    filter: str = ''
    min_flash: int = 32
    arch_allow: set = field(default_factory=set)
    arch_exclude: set = field(default_factory=set)
    build_only: bool = False
    build_on_all: bool = False
    skip: bool = False
    slow: bool = False
    timeout: int = 60
    min_ram: int = 8
    depends_on: set = field(default_factory=set)
    harness: str = ''
    extra_sections: list = field(default_factory=list)
    extra_configs: list[str] = field(default_factory=list)
    extra_args: list[str] = field(default_factory=list)
    integration_platforms: list = field(default_factory=list)
    platform_allow: set = field(default_factory=set)
    platform_exclude: set = field(default_factory=set)
    harness_config: dict = field(default_factory=dict)
    toolchain_exclude: set = field(default_factory=set)
    toolchain_allow: set = field(default_factory=set)

    def __post_init__(self):
        self.tags = _string_to_set(self.tags)
        self.platform_allow = _string_to_set(self.platform_allow)
        self.platform_exclude = _string_to_set(self.platform_exclude)
        self.toolchain_exclude = _string_to_set(self.toolchain_exclude)
        self.toolchain_allow = _string_to_set(self.toolchain_allow)
        self.arch_allow = _string_to_set(self.arch_allow)
        self.arch_exclude = _string_to_set(self.arch_exclude)
        self.depends_on = _string_to_set(self.depends_on)
        self.extra_sections = _string_to_list(self.extra_sections)
        self.extra_configs = _string_to_list(self.extra_configs)
        self.extra_args = _string_to_list(self.extra_args)
        self.integration_platforms = _string_to_list(self.integration_platforms)


def _string_to_set(value: str | set) -> set[str]:
    if isinstance(value, str):
        return set(value.split())
    else:
        return value


def _string_to_list(value: str | list) -> list[str]:
    if isinstance(value, str):
        return list(value.split())
    else:
        return value

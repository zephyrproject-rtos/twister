from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from twister2.helper import string_to_set, string_to_list


@dataclass
class YamlTestSpecification:
    """Test specification for yaml test."""
    name: str  #: test case name plus platform
    original_name: str  #: keeps test case name without platform
    path: Path  #: path to a folder where C files are stored
    rel_to_base_path: Path  #: path relative to zephyr base
    platform: str  #: platform name used for this test
    build_dir: Optional[Path] = None  #: path to dir with build results
    tags: set[str] = field(default_factory=set)
    type: str = 'integration'
    filter: str = ''
    min_flash: int = 32
    arch_allow: set[str] = field(default_factory=set)
    arch_exclude: set[str] = field(default_factory=set)
    build_only: bool = False
    build_on_all: bool = False
    skip: bool = False
    slow: bool = False
    timeout: int = 60
    timeout_multiplier: int = 1
    min_ram: int = 8
    depends_on: set[str] = field(default_factory=set)
    harness: str = ''
    extra_sections: list[str] = field(default_factory=list)
    extra_configs: list[str] = field(default_factory=list)
    extra_args: list[str] = field(default_factory=list)
    integration_platforms: list[str] = field(default_factory=list)
    platform_allow: set[str] = field(default_factory=set)
    platform_exclude: set[str] = field(default_factory=set)
    harness_config: dict = field(default_factory=dict)
    toolchain_exclude: set[str] = field(default_factory=set)
    toolchain_allow: set[str] = field(default_factory=set)

    def __post_init__(self):
        self.tags = string_to_set(self.tags)
        self.platform_allow = string_to_set(self.platform_allow)
        self.platform_exclude = string_to_set(self.platform_exclude)
        self.toolchain_exclude = string_to_set(self.toolchain_exclude)
        self.toolchain_allow = string_to_set(self.toolchain_allow)
        self.arch_allow = string_to_set(self.arch_allow)
        self.arch_exclude = string_to_set(self.arch_exclude)
        self.depends_on = string_to_set(self.depends_on)
        self.extra_sections = string_to_list(self.extra_sections)
        self.extra_configs = string_to_list(self.extra_configs)
        self.extra_args = string_to_list(self.extra_args)
        self.integration_platforms = string_to_list(self.integration_platforms)
        self.timeout *= self.timeout_multiplier

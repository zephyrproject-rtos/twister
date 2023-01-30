from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from marshmallow import Schema, ValidationError, fields, validate

from twister2.constants import QEMU_FIFO_FILE_NAME
from twister2.exceptions import TwisterConfigurationException
from twister2.helper import string_to_list, string_to_set

logger = logging.getLogger(__name__)

SUPPORTED_HARNESSES: list[str] = ['', 'test', 'ztest', 'console']


@dataclass
class YamlTestSpecification:
    """Test specification for yaml test."""
    name: str  #: test case name plus platform
    original_name: str  #: keeps test case name without platform
    source_dir: Path  #: path to a folder where C files are stored
    rel_to_base_path: Path  #: path relative to zephyr base
    platform: str  #: platform name used for this test
    build_name: str = ''  #: name of build configuration from yaml
    output_dir: Path = Path('.')  #: path to dir with build results
    runnable: bool = True
    run_id: str = ''  # unique id passed to building process and verified during ztest test output analysis
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
    min_ram: int = 8
    depends_on: set[str] = field(default_factory=set)
    harness: str = ''
    extra_sections: list[str] = field(default_factory=list)
    extra_configs: list[str] = field(default_factory=list)
    extra_args: list[str] = field(default_factory=list)
    integration_platforms: list[str] = field(default_factory=list)
    ignore_faults: bool = False
    ignore_qemu_crash: bool = False
    platform_allow: set[str] = field(default_factory=set)
    platform_exclude: set[str] = field(default_factory=set)
    platform_key: list[str] = field(default_factory=list)
    platform_type: list[str] = field(default_factory=list)
    harness_config: dict = field(default_factory=dict)
    toolchain_exclude: set[str] = field(default_factory=set)
    toolchain_allow: set[str] = field(default_factory=set)
    modules: list[str] = field(default_factory=list)
    testcases: list[str] = field(default_factory=list)
    sysbuild: bool = False

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
        self.extra_args = string_to_list(self.extra_args)
        self.integration_platforms = string_to_list(self.integration_platforms)

    @property
    def scenario(self):
        return self.build_name or self.original_name

    @property
    def build_dir(self) -> Path:
        return (
            self.output_dir / self.platform / self.rel_to_base_path / self.scenario
        )

    @property
    def fifo_file(self) -> Path:
        return self.build_dir / QEMU_FIFO_FILE_NAME


# Using marshmallow to validate specification from yaml
class HarnessConfigSchema(Schema):
    type = fields.Str()
    fixture = fields.Str()
    ordered = fields.Bool()
    repeat = fields.Int()
    pytest_root = fields.Str()
    pytest_args = fields.List(fields.Str())
    regex = fields.List(fields.Str())
    record = fields.Dict(fields.Str(), fields.Str())


class SampleSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str()


class TestSchema(Schema):
    arch_exclude = fields.Str()
    arch_allow = fields.Str()
    testcases = fields.List(fields.Str)
    build_only = fields.Bool()
    build_on_all = fields.Bool()
    depends_on = fields.Str()
    extra_args = fields.Str()
    extra_configs = fields.List(fields.Str())
    extra_sections = fields.Str()
    filter = fields.Str()
    integration_platforms = fields.List(fields.Str())
    ignore_faults = fields.Bool()
    ignore_qemu_crash = fields.Bool()
    harness = fields.Str()
    harness_config = fields.Nested(HarnessConfigSchema())
    min_ram = fields.Int()
    min_flash = fields.Int()
    modules = fields.List(fields.Str())
    platform_exclude = fields.Str()
    platform_allow = fields.Str()
    platform_key = fields.List(fields.Str())
    platform_type = fields.List(fields.Str())
    tags = fields.Str()
    timeout = fields.Int()
    toolchain_exclude = fields.Str()
    toolchain_allow = fields.Str()
    type = fields.Str(validate=validate.OneOf(['unit']))
    skip = fields.Bool()
    slow = fields.Bool()
    sysbuild = fields.Bool()
    source_dir = fields.Str()


class CommonSchema(TestSchema):
    pass


class YamlTestSpecificationSchema(Schema):
    common = fields.Nested(CommonSchema())
    sample = fields.Nested(SampleSchema())
    tests = fields.Dict(fields.Str(), fields.Nested(TestSchema(), allow_none=True), required=True)


def validate_test_specification_data(data: dict) -> dict:
    """
    Validate test specification data.

    :param data: dictionary to validate
    :return: validated data
    """
    try:
        return YamlTestSpecificationSchema().load(data)
    except ValidationError as exc:
        message = f'Test specification data is not valid: {exc.messages}'
        logger.error(message)
        raise TwisterConfigurationException(message)

import textwrap

import pytest
import yaml

from twister2.exceptions import TwisterConfigurationException
from twister2.yaml_test_specification import (
    YamlTestSpecification,
    validate_test_specification_data,
)

yaml_content = textwrap.dedent("""\
sample:
    description: Hello World sample, the simplest Zephyr
    name: hello world
common:
    tags: introduction
    timeout: 5
    integration_platforms:
        - native_posix
    ignore_faults: True
    ignore_qemu_crash: True
    platform_allow: native_posix native_posix_64 qemu_x86
    platform_exclude: qemu_cortex_m3
    platform_type:
        - mcu
        - native
    harness: console
    harness_config:
        type: one_line
        regex:
            - "Hello World! (.*)"
        ordered: true
        fixture: dummy
        record:
            regex: "(?P<metric>.*):(?P<cycles>.*) cycles ,(?P<nanoseconds>.*) ns"
        pytest_root: foo
        pytest_args:
            - dummy item
        repeat: 1
    min_ram: 20
    min_flash: 1024
    filter: not CONFIG_TRUSTED_EXECUTION_NONSECURE
    extra_configs:
      - CONFIG_NO_OPTIMIZATIONS=y
      - CONFIG_IDLE_STACK_SIZE=512
    arch_exclude: arm64
    arch_allow: arm
    testcases:
        - sem_take_no_wait
        - sem_take_timeout_forever
    build_only: true
    build_on_all: true
    depends_on: usb_device
    skip: true
    slow: true
    sysbuild: true
    modules:
        - fatfs
tests:
    test_hello_world:
        tags: introduction
        type: unit
    test_foo:
        tags: introduction
        timeout: 5
        integration_platforms:
            - native_posix
        ignore_faults: True
        ignore_qemu_crash: True
        platform_allow: native_posix native_posix_64 qemu_x86
        platform_exclude: qemu_cortex_m3
        platform_type:
            - mcu
            - native
        harness: console
        harness_config:
            type: one_line
            regex:
                - "Hello World! (.*)"
        min_ram: 20
        min_flash: 1024
        filter: not CONFIG_TRUSTED_EXECUTION_NONSECURE
        extra_configs:
          - CONFIG_NO_OPTIMIZATIONS=y
          - CONFIG_IDLE_STACK_SIZE=512
        arch_exclude: arm64
        arch_allow: arm
        testcases:
            - sem_take_no_wait
            - sem_take_timeout_forever
        build_only: true
        build_on_all: true
        depends_on: usb_device
        skip: true
        slow: true
        sysbuild: true
    test_bar:
""")


@pytest.fixture
def yaml_specification() -> dict:
    """Return valid specification"""
    return yaml.safe_load(yaml_content)


def test_if_valid_specification_passes_validation(yaml_specification):
    data = validate_test_specification_data(yaml_specification)
    assert isinstance(data, dict)
    assert 'sample' in data
    assert 'common' in data
    assert 'tests' in data


def test_if_invalid_specification_raises_validation_error_for_missing_required_field(yaml_specification):
    yaml_specification.pop('tests')
    with pytest.raises(TwisterConfigurationException, match=r"{'tests': \['Missing data for required field.'\]}"):
        validate_test_specification_data(yaml_specification)


def test_if_invalid_specification_raises_validation_error_for_unknown_field(yaml_specification):
    yaml_specification['foo'] = 'bar'
    with pytest.raises(TwisterConfigurationException, match=r"{'foo': \['Unknown field.'\]}"):
        validate_test_specification_data(yaml_specification)


def test_if_invalid_specification_raises_validation_error_for_unknown_field_in_tests(yaml_specification):
    yaml_specification['tests']['test_foo']['bar'] = 10
    with pytest.raises(
        TwisterConfigurationException, match=r"{'test_foo': {'value': {'bar': \['Unknown field.'\]}}}"
    ):
        validate_test_specification_data(yaml_specification)


def test_if_invalid_specification_raises_validation_error_for_invalid_input_type(yaml_specification):
    yaml_specification['tests']['tags'] = 10
    with pytest.raises(
        TwisterConfigurationException, match=r"{'tags': {'value': {'_schema': \['Invalid input type.'\]}}}"
    ):
        validate_test_specification_data(yaml_specification)


def test_if_can_create_test_specification_instance_from_dict(yaml_specification):
    params = yaml_specification['tests']['test_foo']
    params['name'] = 'test_foo'
    params['original_name'] = 'test_foo'
    params['path'] = '/tmp'
    params['rel_to_base_path'] = '/tmp'
    params['platform'] = 'native_posix'
    YamlTestSpecification(**params)

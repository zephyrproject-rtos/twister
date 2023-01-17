from twister2.yaml_file import read_test_specifications_from_yaml


def test_if_can_read_test_specifications_from_yaml_common(twister_config, resources):
    yaml_file_path = resources / 'tests' / 'common' / 'testcase.yaml'
    for spec in read_test_specifications_from_yaml(yaml_file_path, twister_config):
        if spec.original_name == 'xyz.common_merge_1':
            assert spec.tags == {'kernel', 'posix', 'picolibc'}
            assert spec.extra_configs == ['CONFIG_NEWLIB_LIBC=y', 'CONFIG_POSIX_API=y']
            assert spec.min_ram == 64
        elif spec.original_name == 'xyz.common_merge_2':
            assert spec.tags == {'kernel', 'posix', 'arm'}
            assert spec.extra_configs == ['CONFIG_POSIX_API=y']
            assert spec.min_ram == 32

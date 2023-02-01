import argparse
import json

expected_statuses = ['passed', 'failed', 'error', 'skipped', 'filtered']


def parse_v1_tests(data):
    tests = set()
    for test in data['testsuites']:
        if test['status'] not in expected_statuses:
            continue
        if test['status'] == 'filtered':
            test['status'] = 'skipped'
        suite, test_name = test['name'].rsplit('/', 1)
        name = f'{suite}::{test_name}[{test["platform"]}][{test["status"]}]'
        tests.add(name)
    return tests


def parse_v2_tests(data):
    tests = set()
    for test in data['tests']:
        if test['status'] not in expected_statuses:
            continue
        name = f'{test["nodeid"]}[{test["status"]}]'.replace('/testcase.yaml', '').replace('/sample.yaml', '')
        tests.add(name)
    return tests


def load_data(filename):
    with open(filename) as file:
        return json.load(file)


def dump_tests(tests, filename):
    with open(filename, 'w') as f:
        for test in tests:
            f.write(f'{test}\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--v1', action='store', help='JSON report in V1 format', required=True)
    parser.add_argument('--v2', action='store', help='JSON report in V2 format', required=True)
    args = parser.parse_args()
    v1_report = args.v1
    v2_report = args.v2
    v1_data = load_data(v1_report)
    v2_data = load_data(v2_report)

    tests_v1 = parse_v1_tests(v1_data)
    tests_v2 = parse_v2_tests(v2_data)

    """
    print(' tests v1: '.center(80, '='))
    for test in tests_v1:
        print(test)
    print(f' total {len(tests_v1)} '.center(80, '-'))

    print(' tests v2: '.center(80, '='))
    for test in tests_v2:
        print(test)
    print(f' total {len(tests_v2)} '.center(80, '-'))
    """

    print(' appeared in both: ' .center(80, '='))
    common_set = tests_v1 & tests_v2
    for test in common_set:
        print(test)
    print('total common:', len(common_set))

    print(' missing in v2: '.center(80, '='))
    tests_diff_v1v2 = tests_v1.difference(tests_v2)
    for test in tests_diff_v1v2.copy():
        # V2 doesn't store descoped (filtered) tests
        if '[skipped]' in test:
            tests_diff_v1v2.remove(test)
            continue
        print(test)
    print('total diff:', len(tests_diff_v1v2))

    print(' missing in v1: '.center(80, '='))
    for test in tests_v2.difference(tests_v1):
        print(test)
    print('total diff:', len(tests_v2.difference(tests_v1)))

    dump_tests(tests_v1, 'tests_v1.txt')
    dump_tests(tests_v2, 'tests_v2.txt')


if __name__ == '__main__':
    main()

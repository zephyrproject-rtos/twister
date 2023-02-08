import argparse
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from yaml import safe_load

logger = logging.getLogger(__name__)


@dataclass
class TestData:
    name: str
    t1_cmd: str
    t2_cmd: str
    compare_only_status: bool = False
    t1_outdir: str = 'twister-out-v1'
    t2_outdir: str = 'twister-out-v2'
    returncode: int = 0

    def __post_init__(self):
        currdir = os.getcwd()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.t1_cmd = self.t1_cmd.format(currdir=dir_path)
        self.t1_outdir = f'{currdir}/twister-out-v1/{self.name}'
        self.t1_cmd += f' -c --outdir {self.t1_outdir}'

        self.t2_cmd = self.t2_cmd.format(currdir=currdir)
        self.t2_outdir = f'{currdir}/twister-out-v2/{self.name}'
        self.t2_cmd += f' --clear=delete --outdir={self.t2_outdir}'


class TwisterCommandRunner:
    def __init__(self, ):
        self.procs: list[subprocess.Popen] = []
        self.returncode = 0

    def start_command(self, command):
        env = os.environ.copy()
        proc = subprocess.Popen(command, env=env, shell=True, text=True,
                                cwd=os.environ['ZEPHYR_BASE'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.debug('Execute: %s' % command)
        self.procs.append(proc)

    def wait_for_finish_commands(self):
        for proc in self.procs:
            _out, _err = proc.communicate()
            if proc.returncode != 0:
                logger.warning(_err)
                self.returncode = proc.returncode


def load_data(filename: Path):
    with open(filename) as file:
        return json.load(file)


@dataclass
class ResultElement:
    status: str
    runnable: str = ''


class TwisterResultsComparator:

    def __init__(self, t1_report, t2_report):
        self.tests_v1: dict(ResultElement) = self.parse_v1_tests(load_data(t1_report))
        self.tests_v2: dict(ResultElement) = self.parse_v2_tests(load_data(t2_report))
        self.dump(t1_report.parent, t2_report.parent)
        self.returncode = 0

    def parse_v1_tests(self, data):
        tests = dict()
        for test in data['testsuites']:
            status = test.get('status', 'null')
            if status == 'filtered':
                status = 'skipped'
            suite, test_name = test['name'].rsplit('/', 1)
            name = f'{suite}::{test_name}[{test["platform"]}]'
            tests[name] = ResultElement(status, test['runnable'])
            for subtest in test['testcases']:
                _, subname = subtest['identifier'].rsplit(test_name, 1)
                if subname:
                    tests[name + ' ' + subname] = ResultElement(subtest['status'])
        return tests

    def parse_v2_tests(self, data):
        tests = dict()
        for test in data['tests']:
            status = test.get('status', 'null')
            if 'nodeid' not in test:
                test['nodeid'] = f'{test["path"]}::{test["test_name"]}'
            name = f'{test["nodeid"]}'.replace('/testcase.yaml', '').replace('/sample.yaml', '')
            tests[name] = ResultElement(status, test['runnable'])
            if 'subtests' not in test:
                continue
            for subtest in test['subtests']:
                tests[name + ' .' + subtest['name']] = ResultElement(subtest['status'])
        return tests

    def check_if_found_same_entries(self, status_list):
        only_in_t1 = [
            test_key for test_key, el in self.tests_v1.items()
            if el.status in status_list and test_key not in self.tests_v2
        ]
        if only_in_t1:
            logger.warning('Only in T1:\n{}'.format('\n'.join(only_in_t1)))
            self.returncode += 1

        only_in_t2 = [
            test_key for test_key, el in self.tests_v2.items()
            if el.status in status_list and test_key not in self.tests_v1
        ]
        if only_in_t2:
            logger.warning('Only in T2:\n{}'.format('\n'.join(only_in_t2)))
            self.returncode += 1

    def compare_common_entries(self, compare_only_status=False):
        different_field = []
        for test_key, el in self.tests_v1.items():
            if test_key in self.tests_v2:
                el2 = self.tests_v2[test_key]
                if compare_only_status:
                    if el.status != el2.status:
                        different_field.append(f'{test_key} t1:{el.status}, t2:{el2.status}')
                else:
                    if el != el2:
                        different_field.append(f'{test_key} t1:{el}, t2:{el2}')

        if different_field:
            logger.warning('Results does not match:\n{}'.format('\n'.join(different_field)))
            self.returncode += 1

    def dump(self, t1_dir: Path, t2_dir: Path):
        with open(t1_dir / 'dump.txt', 'w') as f:
            for test, el in sorted(self.tests_v1.items()):
                f.write(f'{test}[{el.status}]\n')
        with open(t2_dir / 'dump.txt', 'w') as f:
            for test, el in sorted(self.tests_v2.items()):
                f.write(f'{test}[{el.status}]\n')


def execute_commands(commands_data, filter_test=None):
    for data_element in commands_data:
        test_data = TestData(**data_element)
        if filter_test:
            if not re.fullmatch(filter_test, test_data.name):
                logger.info(f'Skipped == {test_data.name} == scenario')
                continue
        logger.info(f'Start == {test_data.name} == scenario')
        runner = TwisterCommandRunner()
        runner.start_command(test_data.t1_cmd)
        runner.start_command(test_data.t2_cmd)
        runner.wait_for_finish_commands()
        test_data.returncode = runner.returncode
        # pytest returns 5 if does not collect any tests
        if test_data.returncode == 5:
            test_data.returncode = 0
        yield test_data


def compare_results(test_data: TestData):
    result_file_v1 = Path(test_data.t1_outdir) / 'twister.json'
    result_file_v2 = Path(test_data.t2_outdir) / 'twister.json'
    if not result_file_v1.exists() or not result_file_v2.exists():
        logger.info('Tests not runned, compare only testplans')
        result_file_v1 = Path(test_data.t1_outdir) / 'testplan.json'
        result_file_v2 = Path(test_data.t2_outdir) / 'testplan.json'

    comparator = TwisterResultsComparator(result_file_v1, result_file_v2)
    comparator.compare_common_entries(test_data.compare_only_status)
    comparator.check_if_found_same_entries(status_list=['null', 'passed', 'failed'])
    return comparator.returncode


def run_and_compare(args):
    with open(args.commands_file, 'r', encoding='UTF-8') as yaml_fd:
        commands_data = safe_load(yaml_fd)

    scenarios_with_problems = set()
    for test_data in execute_commands(commands_data, args.filter_test):
        if test_data.returncode != 0:
            logger.error(f'Error in == {test_data.name} == scenario')
            scenarios_with_problems.add(test_data.name)
            continue

        if compare_results(test_data) != 0:
            scenarios_with_problems.add(test_data.name)

    if scenarios_with_problems:
        logger.info('Scenarios with problems: {}'.format(', '.join(scenarios_with_problems)))
    return len(scenarios_with_problems)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('commands_file', metavar='path',
                        help='Yaml file with twister commands to compare')
    parser.add_argument('--filter-test', help='Filter tests name from command file, use regexp')
    parser.add_argument('-ll', '--log-level', type=str.upper, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(levelname)-8s %(lineno)3d:  %(message)s')
    logger = logging.getLogger('compare_results')
    assert os.environ['ZEPHYR_BASE']

    run_and_compare(args)

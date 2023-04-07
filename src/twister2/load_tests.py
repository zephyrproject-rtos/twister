"""
Plugin generates tests from testplan.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import pytest

from twister2.platform_specification import PlatformSpecification
from twister2.specification_processor import YamlSpecificationProcessor
from twister2.twister_config import TwisterConfig
from twister2.yaml_test_function import YamlFunction, yaml_test_function_factory

logger = logging.getLogger(__name__)


@dataclass
class LoadedTestData:
    """Keep data loaded from testplan required to generate test item"""
    testfile: Path = Path('.')
    testname: str = ''
    platform: str = ''
    status: str | None = None
    run_id: str | None = None
    retries: int = 0

    @classmethod
    def load_from_testplan(cls, filename: str | Path) -> Generator[LoadedTestData, None, None]:
        with open(filename) as file:
            test_data = json.load(file)
        for ts in test_data['testsuites']:
            if 'nodeid' in ts and '.py::' in ts['nodeid']:
                logger.debug('Not supported for regular python tests: %s' % ts['nodeid'])
                continue
            testdir, testname = ts['name'].rsplit('/', 1)
            testfile = Path(testdir) / 'testcase.yaml'
            if not testfile.exists():
                testfile = Path(testdir) / 'sample.yaml'
                if not testfile.exists():
                    logger.info(f'Not found yaml test file in {testdir}')
                    continue
            yield LoadedTestData(
                testfile=testfile,
                testname=testname,
                platform=ts['platform'],
                status=ts.get('status', None),
                run_id=ts.get('run_id', None),
                retries=ts.get('retries', 0),
            )


class LoadedTest(pytest.File):
    """Class for collecting tests from a testplan file."""


def collect_tests_from_testplan(twister_config: TwisterConfig, session) -> Generator[YamlFunction, None, None]:
    """Return a list of yaml tests."""

    for loaded in LoadedTestData.load_from_testplan(twister_config.load_tests_path):
        if twister_config.only_failed and loaded.status not in ['error', 'failed']:
            continue

        processor = YamlSpecificationProcessor(twister_config, loaded.testfile)
        platform_spec: PlatformSpecification = twister_config.get_platform(loaded.platform)
        test_spec_dict = processor.prepare_spec_dict(platform_spec, loaded.testname)
        test_spec = processor.create_spec_from_dict(test_spec_dict, platform_spec)

        if loaded.run_id:
            test_spec.run_id = loaded.run_id
        if loaded.status in ['error', 'failed']:
            test_spec.retries = loaded.retries + 1

        node = LoadedTest.from_parent(parent=session, path=loaded.testfile, nodeid=str(loaded.testfile))
        test_function: YamlFunction = yaml_test_function_factory(spec=test_spec, parent=node)
        yield test_function


class LoadTestPlugin:

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(
        self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ):
        if not config.twister_config.load_tests_path:  # type: ignore
            return

        for test in collect_tests_from_testplan(config.twister_config, session):  # type: ignore
            session.items.append(test)

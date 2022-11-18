from __future__ import annotations

import pytest
import logging

from pathlib import Path
from yaml import safe_load
from marshmallow import Schema, fields, ValidationError  # validates
from dataclasses import dataclass, field

from twister2.filter.filter_interface import FilterInterface
from twister2.report.helper import get_test_name, get_item_platform
from twister2.exceptions import TwisterConfigurationException

logger = logging.getLogger(__name__)


class QuarantineFilter(FilterInterface):
    """Filter tests under quarantine."""

    def __init__(self, config: pytest.Config) -> None:
        """
        :param config: pytest configuration
        """
        super().__init__(config)
        self.quarantine_verify = True if 'quarantine' in config.getoption('-m') else False
        self.quarantine = QuarantineData()
        for quarantine_file in config.getoption('--quarantine-list'):
            self.quarantine.extend(QuarantineData.load_data_from_yaml(quarantine_file))

    def pytest_collection_modifyitems(
        self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ):
        for item in items:
            if qelem := self.quarantine.get_matched_quarantine(item):
                item.add_marker(pytest.mark.quarantine(qelem.comment))
                # do not mark tests to be skipped if want to verify quarantined tests
                if not self.quarantine_verify:
                    item.add_marker(pytest.mark.skip('under quarantine'))
                    logger.debug("Skipped test %s - quarantine reason: %s" % (get_test_name(item), qelem.comment))


@dataclass
class QuarantineElem:
    scenarios: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    architectures: list[str] = field(default_factory=list)
    comment: str = 'under quarantine'

    def __post_init__(self):
        if 'all' in self.scenarios:
            self.scenarios = []
        if 'all' in self.platforms:
            self.platforms = []
        if 'all' in self.architectures:
            self.architectures = []
        if not any([self.scenarios, self.platforms, self.architectures]):
            raise TwisterConfigurationException("At least one of filters ('scenarios', 'platforms', "
                                                "'architectures') must be specified")


@dataclass
class QuarantineData:
    qlist: list[QuarantineElem] = field(default_factory=list)

    def __post_init__(self):
        qelements = []
        for qelem in self.qlist:
            qelements.append(QuarantineElem(**qelem))
        self.qlist = qelements

    @classmethod
    def load_data_from_yaml(cls, filename: str | Path):
        """Load quarantine from yaml file."""
        with open(filename, 'r', encoding='UTF-8') as yaml_fd:
            qlist: list(dict) = safe_load(yaml_fd)
        try:
            qlist = QuarantineSchema(many=True).load(qlist)
            return cls(qlist)

        except ValidationError as e:
            logger.error(f'When loading {filename} received error: {e}')
            raise TwisterConfigurationException('Cannot load Quarantine data') from e

    def extend(self, qdata: QuarantineData):
        self.qlist.extend(qdata.qlist)

    def get_matched_quarantine(self, item: pytest.Item) -> QuarantineElem | None:
        """Return quarantine element if test is matched to quarantine rules"""
        scenario = item.originalname
        platform = get_item_platform(item)
        architecture = item.config.twister_config.get_platform(platform).arch if platform else ''

        for qelem in self.qlist:
            matched: bool = False
            if qelem.scenarios:
                if scenario in qelem.scenarios:
                    matched = True
                else:
                    matched = False
                    continue
            if qelem.platforms:
                if platform in qelem.platforms:
                    matched = True
                else:
                    matched = False
                    continue
            if qelem.architectures:
                if architecture in qelem.architectures:
                    matched = True
                else:
                    matched = False
                    continue
            if matched:
                return qelem

        return None


class QuarantineSchema(Schema):
    """ Schema to validata entries in the quarantine yaml file"""
    scenarios = fields.List(fields.String)
    platforms = fields.List(fields.String)
    architectures = fields.List(fields.String)
    comment = fields.String()

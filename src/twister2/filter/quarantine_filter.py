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
        self.quarantine_verify = config.getoption('--quarantine-verify')
        self.quarantine = QuarantineData()
        for quarantine_file in config.getoption('--quarantine-list'):
            self.quarantine.extend(QuarantineData.load_data_from_yaml(quarantine_file))

    def filter(self, item: pytest.Item) -> bool:
        """
        Check if test should be deselected

        :param item: pytest test item
        :return: True if test should be deselected
        """
        if qelem := self.quarantine.get_matched_quarantine(item):
            if not self.quarantine_verify:
                logger.debug(f"Skipped test {get_test_name(item)} - quarantine reason: {qelem.comment}")
                # only mark test to be skipped, this test still will be listed in test plan,
                # but will not be executed
                item.add_marker(pytest.mark.skip(f'Quarantine: {qelem.comment}'))
        else:
            if self.quarantine_verify:
                logger.debug(f"Skipped tests {get_test_name(item)} - not under quarantine")
                return True
        return False


@dataclass
class QuarantineElem:
    scenarios: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    architectures: list[str] = field(default_factory=list)
    comment: str = 'NA'

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
        architecture = item.config.twister_config.get_platform(platform).arch

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

from __future__ import annotations

import pytest
import logging

from pathlib import Path
from yaml import safe_load
from marshmallow import Schema, fields, ValidationError
from dataclasses import dataclass, field

from twister2.report.helper import get_test_name, get_item_platform
from twister2.exceptions import TwisterConfigurationException

logger = logging.getLogger(__name__)


class QuarantinePlugin:
    """Handle tests under quarantine"""

    def __init__(self, config: pytest.Config) -> None:
        """
        :param config: pytest configuration
        """
        self.quarantine_verify = 'quarantine' in config.getoption('-m')
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
                    logger.debug('Skipped test %s - quarantine reason: %s' % (get_test_name(item), qelem.comment))


@dataclass
class QuarantineElement:
    scenarios: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    architectures: list[str] = field(default_factory=list)
    comment: str = 'under quarantine'

    def __post_init__(self):
        # If there is no entry in filters then take all possible values.
        # To keep backward compatibility, 'all' keyword might be still used.
        if 'all' in self.scenarios:
            self.scenarios = []
        if 'all' in self.platforms:
            self.platforms = []
        if 'all' in self.architectures:
            self.architectures = []
        # However, at least one of the filters ('scenarios', platforms' ...)
        # must be given (there is no sense to put all possible configuration
        # into quarantine)
        if not any([self.scenarios, self.platforms, self.architectures]):
            raise TwisterConfigurationException(
                "At least one of filters ('scenarios', 'platforms', 'architectures') must be specified")


@dataclass
class QuarantineData:
    qlist: list[QuarantineElement] = field(default_factory=list)

    def __post_init__(self):
        qelements = []
        for qelem in self.qlist:
            if isinstance(qelem, QuarantineElement):
                qelements.append(qelem)
            else:
                qelements.append(QuarantineElement(**qelem))
        self.qlist = qelements

    @classmethod
    def load_data_from_yaml(cls, filename: str | Path) -> QuarantineData:
        """Load quarantine from yaml file."""
        with open(filename, 'r', encoding='UTF-8') as yaml_fd:
            qlist: list(dict) = safe_load(yaml_fd)
        try:
            qlist = QuarantineSchema(many=True).load(qlist)
            return cls(qlist)

        except ValidationError as e:
            logger.error(f'When loading {filename} received error: {e}')
            raise TwisterConfigurationException('Cannot load Quarantine data') from e

    def extend(self, qdata: QuarantineData) -> list[QuarantineElement]:
        self.qlist.extend(qdata.qlist)

    def get_matched_quarantine(self, item: pytest.Item) -> QuarantineElement | None:
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

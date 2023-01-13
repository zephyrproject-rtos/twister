from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from marshmallow import Schema, ValidationError, fields
from yaml import safe_load

from twister2.exceptions import TwisterConfigurationException
from twister2.report.helper import get_item_platform, get_test_name

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
    simulations: list[str] = field(default_factory=list)
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
        if 'all' in self.simulations:
            self.simulations = []
        # However, at least one of the filters ('scenarios', platforms' ...)
        # must be given (there is no sense to put all possible configuration
        # into quarantine)
        if not any([self.scenarios, self.platforms, self.architectures, self.simulations]):
            raise TwisterConfigurationException(
                "At least one of filters ('scenarios', 'platforms' ...) must be specified")


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
            qlist_raw_data: list[dict] = safe_load(yaml_fd)
        try:
            if not qlist_raw_data:
                # in case of loading empty quarantine file
                return cls()
            qlist = QuarantineSchema(many=True).load(qlist_raw_data)
            return cls(qlist)

        except ValidationError as e:
            logger.error(f'When loading {filename} received error: {e}')
            raise TwisterConfigurationException('Cannot load Quarantine data') from e

    def extend(self, qdata: QuarantineData) -> None:
        self.qlist.extend(qdata.qlist)

    def get_matched_quarantine(self, item: pytest.Item) -> QuarantineElement | None:
        """Return quarantine element if test is matched to quarantine rules"""
        scenario = item.originalname  # type: ignore[attr-defined]
        platform = get_item_platform(item)
        if platform:
            plat_spec = item.config.twister_config.get_platform(platform)  # type: ignore
            architecture = plat_spec.arch
            simulation = plat_spec.simulation
        else:
            architecture = ''
            simulation = ''  # type: ignore

        for qelem in self.qlist:
            matched: bool = False
            if (qelem.scenarios
                    and (matched := _is_element_matched(scenario, qelem.scenarios)) is False):
                continue
            if (qelem.platforms
                    and (matched := _is_element_matched(platform, qelem.platforms)) is False):
                continue
            if (qelem.architectures
                    and (matched := _is_element_matched(architecture, qelem.architectures)) is False):
                continue
            if (qelem.simulations
                    and (matched := _is_element_matched(simulation, qelem.simulations)) is False):
                continue

            if matched:
                return qelem
        return None


def _is_element_matched(element: str, list_of_elements: list) -> bool:
    """Return True if given element is matching to any of elements from the list"""
    for pattern in list_of_elements:
        if re.fullmatch(pattern, element):
            return True
    return False


class QuarantineSchema(Schema):
    """ Schema to validata entries in the quarantine yaml file"""
    scenarios = fields.List(fields.String)
    platforms = fields.List(fields.String)
    architectures = fields.List(fields.String)
    simulations = fields.List(fields.String)
    comment = fields.String()

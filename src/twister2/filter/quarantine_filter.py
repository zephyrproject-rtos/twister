from __future__ import annotations

import pytest
import logging

from pathlib import Path
from yaml import safe_load

from twister2.filter.filter_interface import FilterInterface
from twister2.report.helper import get_test_name
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


class QuarantineFilter(FilterInterface):
    """Filter slow tests."""

    def __init__(self, config: pytest.Config) -> None:
        """
        :param config: pytest configuration
        """
        super().__init__(config)
        self.quarantine_verify = config.getoption('--quarantine-verify')
        self.quarantine = {}
        for quarantine_file in config.getoption('--quarantine-list'):
            self._load_quarantine(quarantine_file, config.twister_config)

    def filter(self, item: pytest.Item) -> bool:
        """
        Check if test should be deselected

        :param item: pytest test item
        :return: True if test should be deselected
        """
        test_configuration = get_test_name(item)
        if self.quarantine_verify:
            if test_configuration not in self.quarantine:
                logger.debug(f"Skipped tests {test_configuration} - not under quarantine")
                return True
        else:
            if test_configuration in self.quarantine:
                logger.debug(f"Skipped test {test_configuration} - quarantine reason: "
                             f"{self.quarantine[test_configuration]}")
                # only mark test to be skipped, this test still will be listed in test plan,
                # but will not be executed
                item.add_marker(pytest.mark.skip(f'Quarantine: {self.quarantine[test_configuration]}'))
        return False

    def _load_quarantine(self, filepath: Path, twister_config: TwisterConfig):
        """
        Loads quarantine list from the given yaml file. Creates a dictionary
        of all tests configurations (platform + scenario: comment) that shall be
        skipped due to quarantine
        """
        # Load yaml into quarantine_yaml
        with open(filepath) as yaml_fd:
            quarantine_yaml: dict = safe_load(yaml_fd)

        for quar_dict in quarantine_yaml:
            if quar_dict['platforms'][0] == "all":
                plat_list = [platform for platform in twister_config.default_platforms]
            else:
                plat_list = []
                for p_name in quar_dict['platforms']:
                    platform = twister_config.get_platform(p_name)
                    plat_list.append(platform.identifier)
            comment = quar_dict.get('comment', 'NA')
            for scenario in quar_dict['scenarios']:
                self._update_quarantine_list(plat_list, scenario, comment)

    def _update_quarantine_list(self, platforms: list[str], scenario: str, comment):
        for plat in platforms:
            test_conf = f"{scenario}[{plat}]"
            self.quarantine.update({test_conf: comment})

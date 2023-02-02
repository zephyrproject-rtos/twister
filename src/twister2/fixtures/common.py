"""
Module contains common code for all fixtures.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pytest

from twister2.exceptions import TwisterConfigurationException
from twister2.platform_specification import PlatformSpecification
from twister2.twister_config import TwisterConfig
from twister2.yaml_test_specification import YamlTestSpecification

logger = logging.getLogger(__name__)


@dataclass
class State:
    should_run: bool
    message: str = ''  # message for logging
    reason: str = ''  # skip reason

    def __bool__(self) -> bool:
        return self.should_run


class SetupTestManager:
    """Helper class to handle all setup required for test execution."""

    def __init__(self, request: pytest.FixtureRequest) -> None:
        self.request = request
        self.twister_config: TwisterConfig = request.config.twister_config  # type: ignore
        self.nodeid: str = request.node.nodeid
        self.specification: YamlTestSpecification = request.session.specifications.get(self.nodeid)  # type: ignore
        if not self.specification:
            msg = f'Could not find test specification for test {request.node.nodeid}'
            logger.error(msg)
            raise TwisterConfigurationException(msg)
        self.platform: PlatformSpecification = self.twister_config.get_platform(self.specification.platform)
        self.build_only: bool = self.twister_config.build_only or self.specification.build_only
        self.device_testing: bool = self.twister_config.device_testing
        self.runnable: bool = self.specification.runnable
        self.is_executable: State = self.should_be_executed(
            self.build_only, self.device_testing, self.runnable, self.platform.type, self.platform.simulation
        )

    @staticmethod
    def should_be_executed(build_only: bool, device_testing: bool, runnable: bool, platform_type: str,
                           platform_sim: str) -> State:
        """Verify if test should be executed based on provided factors"""
        if build_only:
            return State(
                False,
                'Skipping test after building due to build-only being selected',
                'Built but not executed due to build-only being selected'
            )
        if platform_type == 'mcu' and device_testing is False and platform_sim == 'na':
            return State(
                False,
                'Skipping test after building because platform type is "mcu", '
                'but device-testing was selected',
                'Built but not executed because device-testing was not selected for platform type mcu'
            )
        if runnable is False:
            return State(
                False,
                'Skipping test after building because it is not runnable',
                'Built but not executed bcause the test is not runnable'
            )
        return State(True)

    def get_device_type(self) -> str:
        if self.platform.type == 'mcu':
            if not self.device_testing and self.platform.simulation != 'na':
                # if device_testing was not chosen but simulation is accessible then try to run on simulator
                pass
            else:
                return 'hardware'
        if self.platform.simulation == 'native':
            return 'native'
        elif self.platform.simulation == 'qemu':
            return 'qemu'
        elif self.platform.simulation != 'na':
            return 'custom'
        elif self.platform.type == 'unit':
            return 'unit'
        else:
            return ''

from __future__ import annotations

import logging

from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.cmake_filter.cmake_filter import CMakeFilter
from twister2.exceptions import TwisterBuildFiltrationException

logger = logging.getLogger(__name__)


class BuildFilterProcessor:
    """Run additional setup before actual build is triggered."""

    def __init__(self, builder: BuilderAbstract) -> None:
        self.builder = builder

    def process(self) -> None:
        """Run build with cmake_helper flag enabled."""
        self.builder.run_cmake_stage(True)
        self.apply_cmake_filtration(self.builder.build_config)

    @staticmethod
    def apply_cmake_filtration(build_config: BuildConfig) -> None:
        cmake_filter = CMakeFilter(
            build_config.zephyr_base,
            build_config.build_dir,
            build_config.platform_arch,
            build_config.platform_name,
            build_config.cmake_filter
        )
        result: bool = cmake_filter.filter()
        if result is False:
            msg = 'runtime filter - build configuration do not fullfil Kconfig, DTS or other CMake requirements'
            logger.info(msg)
            raise TwisterBuildFiltrationException(msg)

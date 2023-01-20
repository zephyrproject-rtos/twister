from __future__ import annotations

import logging

from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.exceptions import TwisterBuildFiltrationException
from twister2.kconfig_dts_filter.kconfig_dts_filter import KconfigDtsFilter

logger = logging.getLogger(__name__)


class BuildFilterProcessor:
    """Run additional setup before actual build is triggered."""

    def __init__(self, builder: BuilderAbstract) -> None:
        self.builder = builder

    def process(self) -> None:
        """Run build with cmake_helper flag enabled."""
        self.builder.build(True)
        self._apply_kconfig_and_dts_filtration(self.builder.build_config)

    def _apply_kconfig_and_dts_filtration(self, build_config: BuildConfig) -> None:
        kconfig_dts_filter = KconfigDtsFilter(
            build_config.zephyr_base,
            build_config.build_dir,
            build_config.platform_arch,
            build_config.platform_name,
            build_config.kconfig_dts_filter
        )
        result: bool = kconfig_dts_filter.filter()
        if result is False:
            raise TwisterBuildFiltrationException(f'{build_config.source_dir}')

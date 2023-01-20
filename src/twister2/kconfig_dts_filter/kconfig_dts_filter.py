from __future__ import annotations

import logging
import os
import pickle
import re
import sys
from pathlib import Path

from twister2.kconfig_dts_filter import expr_parser
from twister2.kconfig_dts_filter.cmakecache import CMakeCache

logger = logging.getLogger(__name__)


class KconfigDtsFilter:
    config_re = re.compile('(CONFIG_[A-Za-z0-9_]+)[=]\"?([^\"]*)\"?$')
    dt_re = re.compile('([A-Za-z0-9_]+)[=]\"?([^\"]*)\"?$')

    def __init__(self, zephyr_base: str | Path, build_dir: str | Path, platform_arch: str, platform_name: str,
                 filter_exp: str) -> None:
        self.build_dir: str = str(build_dir)
        self.platform_arch: str = platform_arch
        self.platform_name: str = platform_name
        self.filter_exp: str = filter_exp

        self.sysbuild: bool = False

        # This is needed to load edt.pickle files by pickle.load().
        sys.path.insert(0, os.path.join(zephyr_base, 'scripts', 'dts',
                                        'python-devicetree', 'src'))
        from devicetree import edtlib  # noqa: F401

    def filter(self) -> bool:

        # # TODO: add handling for unit_testing
        # if self.platform.name == "unit_testing":
        #     return {}

        # # TODO: add handling for sysbuild
        # if self.testsuite.sysbuild:
        #     # Load domain yaml to get default domain build directory
        #     domain_path = os.path.join(self.build_dir, "domains.yaml")
        #     domains = Domains.from_file(domain_path)
        #     logger.debug("Loaded sysbuild domain data from %s" % (domain_path))
        #     domain_build = domains.get_default_domain().build_dir
        #     cmake_cache_path = os.path.join(domain_build, "CMakeCache.txt")
        #     defconfig_path = os.path.join(domain_build, "zephyr", ".config")
        #     edt_pickle = os.path.join(domain_build, "zephyr", "edt.pickle")
        # else:
        cmake_cache_path = os.path.join(self.build_dir, 'CMakeCache.txt')
        defconfig_path = os.path.join(self.build_dir, 'zephyr', '.config')
        edt_pickle = os.path.join(self.build_dir, 'zephyr', 'edt.pickle')

        defconfig = {}
        with open(defconfig_path, 'r') as fp:
            for line in fp.readlines():
                m = self.config_re.match(line)
                if not m:
                    if line.strip() and not line.startswith('#'):
                        sys.stderr.write('Unrecognized line %s\n' % line)
                    continue
                defconfig[m.group(1)] = m.group(2).strip()

        cmake_conf = {}
        try:
            cache = CMakeCache.from_file(cmake_cache_path)
        except FileNotFoundError:
            cache = {}

        for k in iter(cache):
            cmake_conf[k.name] = k.value

        filter_data = {
            'ARCH': self.platform_arch,
            'PLATFORM': self.platform_name
        }
        filter_data.update(os.environ)
        filter_data.update(defconfig)
        filter_data.update(cmake_conf)

        # # TODO: add handling for sysbuild
        # if self.testsuite.sysbuild and self.env.options.device_testing:
        #     # Verify that twister's arguments support sysbuild.
        #     # Twister sysbuild flashing currently only works with west, so
        #     # --west-flash must be passed. Additionally, erasing the DUT
        #     # before each test with --west-flash=--erase will inherently not
        #     # work with sysbuild.
        #     if self.env.options.west_flash is None:
        #         logger.warning("Sysbuild test will be skipped. " +
        #             "West must be used for flashing.")
        #         return {os.path.join(self.platform.name, self.testsuite.name): True}
        #     elif "--erase" in self.env.options.west_flash:
        #         logger.warning("Sysbuild test will be skipped, " +
        #             "--erase is not supported with --west-flash")
        #         return {os.path.join(self.platform.name, self.testsuite.name): True}

        try:
            if os.path.exists(edt_pickle):
                with open(edt_pickle, 'rb') as f:
                    edt = pickle.load(f)
            else:
                edt = None
            result = expr_parser.parse(self.filter_exp, filter_data, edt)

        except (ValueError, SyntaxError) as se:
            sys.stderr.write(
                f'Failed processing kconfig and dts for {self.build_dir}\n')
            raise se

        return result

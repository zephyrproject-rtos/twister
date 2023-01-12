"""
Pytest fixture for building hex files.
"""
import logging
from pathlib import Path
from typing import Generator

import pytest

from twister2.builder.build_manager import BuildManager
from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.builder.factory import BuilderFactory
from twister2.fixtures.common import SetupTestManager
from twister2.yaml_test_function import YamlTestCase

logger = logging.getLogger(__name__)


@pytest.fixture(name='build_manager', scope='function')
def fixture_build_manager(
        request: pytest.FixtureRequest, setup_manager: SetupTestManager
) -> Generator[BuildManager, None, None]:
    """Build manager"""
    spec = setup_manager.specification
    twister_config = setup_manager.twister_config

    spec.output_dir = Path(twister_config.output_dir).resolve()

    builder_type: str = request.config.option.builder
    builder = BuilderFactory.get_builder(builder_type)

    if setup_manager.get_device_type() == 'qemu':
        spec.extra_args.append(f'QEMU_PIPE={spec.fifo_file}')

    build_config = BuildConfig(
        zephyr_base=setup_manager.twister_config.zephyr_base,
        source_dir=spec.source_dir,
        platform=spec.platform,
        build_dir=spec.build_dir,
        scenario=spec.scenario,
        extra_configs=spec.extra_configs,
        extra_args_spec=spec.extra_args,
        extra_args_cli=twister_config.extra_args_cli
    )
    build_manager = BuildManager(request.config.option.output_dir, build_config, builder)
    yield build_manager


@pytest.fixture(name='builder', scope='function')
def fixture_builder(
        request: pytest.FixtureRequest, build_manager: BuildManager
) -> Generator[BuilderAbstract, None, None]:
    """Build hex files for test suite."""
    setup = SetupTestManager(request)

    build_manager.build()

    if not isinstance(request.function, YamlTestCase):
        # skip regular tests
        should_run = setup.is_executable
        if setup.is_executable is False:
            logger.warning(f'{should_run.message}: {request.node.nodeid}')
            pytest.skip(should_run.reason)

    yield build_manager.builder

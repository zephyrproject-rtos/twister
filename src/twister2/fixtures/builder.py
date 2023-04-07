"""
Pytest fixture for building hex files.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

import pytest

from twister2.builder.build_helper import CMakeExtraArgsConfig, CMakeExtraArgsGenerator
from twister2.builder.build_manager import BuildManager
from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.builder.factory import BuilderFactory
from twister2.exceptions import (
    TwisterBuildFiltrationException,
    TwisterBuildSkipException,
    TwisterMemoryOverflowException,
)
from twister2.fixtures.common import SetupTestManager
from twister2.yaml_test_function import YamlTestCase

logger = logging.getLogger(__name__)


@pytest.fixture(name='build_manager', scope='function')
def fixture_build_manager(
        request: pytest.FixtureRequest, setup_manager: SetupTestManager
) -> Generator[BuildManager, None, None]:
    """Build manager"""
    platform = setup_manager.platform
    spec = setup_manager.specification
    twister_config = setup_manager.twister_config

    spec.output_dir = Path(twister_config.output_dir).resolve()

    cmake_args_config = CMakeExtraArgsConfig(
        run_id=spec.run_id,
        extra_args_spec=spec.extra_args,
        extra_configs=spec.extra_configs,
        build_dir=spec.build_dir,
        fifo_file=spec.fifo_file,
        device_type=setup_manager.get_device_type(),
        extra_args_cli=twister_config.extra_args_cli,
        platform_arch=platform.arch,
        platform_name=platform.identifier,
    )

    args_generator = CMakeExtraArgsGenerator(cmake_args_config)
    cmake_extra_args = args_generator.generate()

    build_config = BuildConfig(
        zephyr_base=setup_manager.twister_config.zephyr_base,
        source_dir=spec.source_dir,
        platform_arch=platform.arch,
        platform_name=platform.identifier,
        build_dir=spec.build_dir,
        output_dir=request.config.option.output_dir,
        scenario=spec.scenario,
        cmake_extra_args=cmake_extra_args,
        overflow_as_errors=twister_config.overflow_as_errors,
        cmake_filter=spec.filter,
    )

    builder_type: str = request.config.option.builder
    builder = BuilderFactory.create_instance(builder_type, build_config)
    build_manager = BuildManager(build_config, builder)

    yield build_manager

    if request.config.option.prep_artifacts_for_testing:
        build_manager.prepare_device_testing_artifacts(list(platform.testing.binaries))
    elif (cleanup_version := request.config.option.runtime_artifact_cleanup) is not None:
        test_failed = getattr(request.node, '_test_failed', False)
        if cleanup_version == 'all' or (cleanup_version == 'pass' and not test_failed):
            build_manager.cleanup_artifacts(cleanup_version=cleanup_version)


@pytest.fixture(name='builder', scope='function')
def fixture_builder(
        request: pytest.FixtureRequest,
        build_manager: BuildManager,
        setup_manager: SetupTestManager
) -> Generator[BuilderAbstract, None, None]:
    """Build hex files for test suite."""
    try:
        build_manager.build()
    except TwisterMemoryOverflowException as overflow_exception:
        if setup_manager.twister_config.overflow_as_errors:
            raise
        else:
            pytest.skip(str(overflow_exception))
    except TwisterBuildFiltrationException as filtration_exception:
        pytest.skip(str(filtration_exception))
    except TwisterBuildSkipException as skip_exception:
        pytest.skip(str(skip_exception))

    if not isinstance(request.function, YamlTestCase):
        # skip regular tests
        should_run = setup_manager.is_executable
        if setup_manager.is_executable is False:
            logger.warning(f'{should_run.message}: {request.node.nodeid}')
            pytest.skip(should_run.reason)

    yield build_manager.builder


@pytest.fixture(name='skip_if_not_executable', scope='function')
def fixture_skip_if_not_executable(
    builder: BuilderAbstract,
    setup_manager: SetupTestManager
) -> None:
    """Skip tests after building if not executable"""
    if not setup_manager.is_executable:
        logger.info(f'{setup_manager.is_executable.message}')
        pytest.skip(setup_manager.is_executable.reason)

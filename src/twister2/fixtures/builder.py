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
from twister2.exceptions import TwisterConfigurationException
from twister2.twister_config import TwisterConfig
from twister2.yaml_test_specification import YamlTestSpecification

logger = logging.getLogger(__name__)


@pytest.fixture(name='build_manager', scope='function')
def fixture_build_manager(request: pytest.FixtureRequest) -> Generator[BuildManager, None, None]:
    """Build hex files for test suite."""
    twister_config: TwisterConfig = request.config.twister_config  # type: ignore
    spec: YamlTestSpecification = request.session.specifications.get(request.node.nodeid)  # type: ignore
    if not spec:
        msg = f'Could not find test specification for test {request.node.nodeid}'
        logger.error(msg)
        raise TwisterConfigurationException(msg)

    spec.output_dir = Path(twister_config.output_dir).resolve()

    builder_type: str = request.config.option.builder
    builder = BuilderFactory.get_builder(builder_type)
    build_config = BuildConfig(
        zephyr_base=twister_config.zephyr_base,
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


@pytest.fixture(scope='function')
def builder(build_manager: BuildManager) -> Generator[BuilderAbstract, None, None]:
    build_manager.build()
    yield build_manager.builder

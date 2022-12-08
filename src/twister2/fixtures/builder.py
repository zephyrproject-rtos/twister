"""
Pytest fixture for building hex files.
"""
import logging
from pathlib import Path

import pytest

from twister2.builder.build_manager import BuildManager
from twister2.builder.builder_abstract import BuildConfig, BuilderAbstract
from twister2.builder.factory import BuilderFactory
from twister2.exceptions import TwisterConfigurationException
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def builder(request: pytest.FixtureRequest) -> BuilderAbstract:
    """Build hex files for test suite."""
    twister_config: TwisterConfig = request.config.twister_config
    spec = request.session.specifications.get(request.node.nodeid)
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
        extra_args=spec.extra_args
    )
    build_manager = BuildManager(request.config.option.output_dir)
    build_manager.build(builder, build_config)
    yield builder

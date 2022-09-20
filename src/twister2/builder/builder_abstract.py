from __future__ import annotations

import abc
import contextlib
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class BuilderAbstract(abc.ABC):
    """Base class for builders."""

    def __init__(self, zephyr_base: str | Path, source_dir: str | Path):
        """
        :param zephyr_base: path to zephyr directory
        :param source_dir: path to test source directory
        """
        self.zephyr_base: Path = Path(zephyr_base)
        self.source_dir: Path = Path(source_dir)

    def __repr__(self):
        return f'{self.__class__.__name__}(zephyr_base={self.zephyr_base!r}, source_dir={self.source_dir!r})'

    @property
    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env['ZEPHYR_BASE'] = str(self.zephyr_base)
        return env

    @abc.abstractmethod
    def build(self, platform: str, scenario: str, build_dir: str | Path | None = None, **kwargs) -> None:
        """Build Zephyr application."""

    @contextlib.contextmanager
    def set_directory(self, path: Path) -> None:
        origin = Path().absolute()
        try:
            logger.debug('Changing directory to "%s"', path)
            os.chdir(path)
            yield
        finally:
            os.chdir(origin)

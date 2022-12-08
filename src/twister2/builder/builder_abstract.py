from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BuildConfig:
    zephyr_base: str | Path
    source_dir: str | Path
    build_dir: str | Path
    platform: str
    scenario: str
    extra_args: list[str] = field(default_factory=list)


class BuilderAbstract(abc.ABC):
    """Base class for builders."""

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    @abc.abstractmethod
    def build(self, build_config: BuildConfig) -> None:
        """
        Build Zephyr application.

        :param build_config: build configuration
        """

from __future__ import annotations

import logging
from typing import Type

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.builder.west_builder import WestBuilder

logger = logging.getLogger(__name__)


class BuilderFactory:
    _builders: dict[str, Type[BuilderAbstract]] = {}

    @classmethod
    def register_builder_class(cls, name: str, klass: Type[BuilderAbstract]):
        """Register builder class."""
        if name not in cls._builders:
            cls._builders[name] = klass

    @classmethod
    def get_builder(cls, name: str) -> BuilderAbstract:
        """
        Return builder.

        :param name: builder name
        :return: builder instance
        """
        try:
            return cls._builders[name]()
        except KeyError as e:
            logger.exception('There is not builder with name: %s', name)
            raise KeyError(f'Builder "{name}" does not exist') from e


BuilderFactory.register_builder_class('west', WestBuilder)

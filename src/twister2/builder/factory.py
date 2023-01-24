from __future__ import annotations

import logging
from typing import Type

from twister2.builder.builder_abstract import BuilderAbstract
from twister2.builder.cmake_builder import CMakeBuilder
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
    def get_builder(cls, name: str) -> Type[BuilderAbstract]:
        """
        Return builder class.

        :param name: builder name
        :return: builder instance
        """
        try:
            return cls._builders[name]
        except KeyError as e:
            logger.exception('There is not builder class with name: %s', name)
            raise KeyError(f'Builder class "{name}" does not exist') from e

    @classmethod
    def create_instance(cls, name, *args, **kwargs) -> BuilderAbstract:
        """
        Create new instance of builder.

        :param name: builder name
        :param args: unnamed arguments for builder class
        :param kwargs: named arguments for builder class
        :return: new builder instance
        """
        return cls.get_builder(name)(*args, **kwargs)


BuilderFactory.register_builder_class('cmake', CMakeBuilder)
BuilderFactory.register_builder_class('west', WestBuilder)

from __future__ import annotations

import logging
from typing import Type

from twister2.log_parser.console_log_parser import ConsoleLogParser
from twister2.log_parser.harness_log_parser import HarnessLogParser
from twister2.log_parser.log_parser_abstract import LogParserAbstract

logger = logging.getLogger(__name__)


class LogParserFactory:
    _parsers: dict[str, Type[LogParserAbstract]] = {}

    @classmethod
    def register_device_class(cls, name: str, klass: Type[LogParserAbstract]) -> None:
        if name not in cls._parsers:
            cls._parsers[name] = klass

    @classmethod
    def get_parser(cls, name: str) -> Type[LogParserAbstract]:
        try:
            return cls._parsers[name]
        except KeyError as e:
            logger.exception('There is not parser with name: %s', name)
            raise KeyError(f'Parser "{name}" does not exist') from e


LogParserFactory.register_device_class('harness', HarnessLogParser)
LogParserFactory.register_device_class('console', ConsoleLogParser)

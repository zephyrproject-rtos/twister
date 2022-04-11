from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from twister2.log_parser.log_parser_abstract import LogParserAbstract


@dataclass
class HarnessConfig:
    fail_on_fault: bool = False


# TODO: to be implemented
class ConsoleLogParser(LogParserAbstract):
    """Console log parser."""

    def __init__(self, stream: Iterator[str], *, harness_config: dict, **kwargs):
        super().__init__(stream)
        self.harness_config = harness_config

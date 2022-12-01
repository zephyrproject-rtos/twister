"""
Console log parser
"""
from __future__ import annotations

import logging
import re
import time
from typing import Callable, Iterator

from twister2.exceptions import TwisterHarnessParserException
from twister2.log_parser.log_parser_abstract import LogParserAbstract

logger = logging.getLogger(__name__)

ZEPHYR_FATAL_ERROR: str = 'ZEPHYR FATAL ERROR'

ONE_LINE: str = 'one_line'
MULTI_LINE: str = 'multi_line'


class ConsoleLogParser(LogParserAbstract):
    """Console log parser."""

    def __init__(self, stream: Iterator[str], *, harness_config: dict, **kwargs):
        super().__init__(stream)
        self.harness_config = harness_config
        self.matched_lines: list[str] = []
        self.type: str = harness_config.get('type')
        self.ordered: bool = harness_config.get('ordered', False)
        self.regex: list[str] = harness_config.get('regex', [])
        self.patterns: list[re.Pattern] = []
        self.parse_method = self._get_parse_method()
        for regex in self.regex:
            self.patterns.append(re.compile(regex))

        if not self.patterns:
            raise TwisterHarnessParserException('At least one regex must be provided')

    def _get_parse_method(self) -> Callable[[str], bool]:
        if self.type == ONE_LINE:
            return self._parse_one_line
        elif self.type == MULTI_LINE and self.ordered:
            return self._parse_ordered_multi_lines
        elif self.type == MULTI_LINE and not self.ordered:
            return self._parse_not_ordered_multi_lines
        else:
            logger.error('Unknown harness_config type')
            raise TwisterHarnessParserException('Unknown harness_config type')

    def parse(self, timeout: float = 60) -> None:
        logger.debug('%s: Parsing output', self.__class__.__name__)
        end_time = time.time() + timeout
        while self.stream:
            if time.time() > end_time:
                self.state = self.STATE.FAILED
                self.messages.append(f'Did not find expected messages in {timeout} seconds')
                break

            try:
                line = next(self.stream)
            except StopIteration:
                break

            logger.info(line.rstrip())
            if self.parse_method(line):
                logger.info('Console parser found expected lines')
                break

        if len(self.matched_lines) != len(self.regex):
            self.state = self.STATE.FAILED
            self.messages.append('Did not find expected messages')

    def _parse_one_line(self, line: str) -> bool:
        if self.patterns[0].search(line):
            self.state = self.STATE.PASSED
            self.matched_lines.append(line)
            return True
        return False

    def _parse_ordered_multi_lines(self, line: str) -> bool:
        if self.patterns:
            if self.patterns[0].search(line):
                self.matched_lines.append(line)
                self.patterns.pop(0)

        if len(self.matched_lines) == len(self.regex):
            self.state = self.STATE.PASSED
            return True
        return False

    def _parse_not_ordered_multi_lines(self, line: str) -> bool:
        for idx, pattern in enumerate(self.patterns):
            if pattern.search(line):
                self.matched_lines.append(line)
                self.patterns.pop(idx)
                break

        if len(self.matched_lines) == len(self.regex):
            self.state = self.STATE.PASSED
            return True
        return False

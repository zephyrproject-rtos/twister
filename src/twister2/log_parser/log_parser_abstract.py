from __future__ import annotations

import abc
import enum
from typing import Iterator


class LogParserState(str, enum.Enum):
    UNKNOWN = 'UNKNOWN'
    FAILED = 'FAILED'
    PASSED = 'PASSED'


class LogParserAbstract(abc.ABC):
    STATE = LogParserState

    def __init__(self, stream: Iterator[str], **kwargs):
        self.stream = stream
        self.state: self.STATE = self.STATE.UNKNOWN  #: overall state for execution test suite
        self.messages: list[str] = []  #: keeps errors from execution

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    @abc.abstractmethod
    def parse(self, timeout: float = 60) -> None:
        """Parse output from device and set appropriate parser status"""

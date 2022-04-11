from __future__ import annotations

import abc
import enum
from dataclasses import dataclass
from typing import Generator, Iterator


class LogParserAbstract(abc.ABC):

    def __init__(self, stream: Iterator[str], **kwargs):
        self.stream = stream
        self.state: str = 'PASSED'  #: overall status for execution suite
        self.messages: list[str] = []  #: keeps errors from execution

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    @abc.abstractmethod
    def parse(self, timeout: float = 60) -> Generator[SubTestResult, None, None] | None:
        """Return results of subtests."""


class SubTestStatus(str, enum.Enum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    SKIP = 'SKIP'

    def __str__(self):
        return self.name


@dataclass
class SubTestResult:
    """Store result for single C tests."""
    testname: str
    result: SubTestStatus
    duration: float

    def __post_init__(self):
        if isinstance(self.duration, str):
            self.duration = float(self.duration)
        if isinstance(self.result, str):
            self.result = SubTestStatus(self.result)

    def asdict(self) -> dict:
        """Return JSON serialized dictionary."""
        return dict(
            testname=self.testname,
            result=str(self.result),
            duration=self.duration
        )

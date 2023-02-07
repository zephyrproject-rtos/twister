from __future__ import annotations

import abc
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class LogFileAbstract(abc.ABC):
    """Base class for logging files."""

    def __init__(self, build_dir: Path | str, name: str) -> None:
        self.default_encoding = sys.getdefaultencoding()
        self.filename = self.get_log_filename(build_dir=build_dir, name=name)

    def get_log_filename(self, build_dir: Path | str, name: str) -> str:
        """
        :param build_dir: path to building directory.
        :param name: name of the logging file.
        :return: path to logging file
        """
        name = name + '.log'
        filename = os.path.join(build_dir, name)
        filename = self._normalize_filename_path(filename=filename)
        return filename

    @staticmethod
    def _normalize_filename_path(filename: str) -> str:
        filename = os.path.expanduser(os.path.expandvars(filename))
        filename = os.path.normpath(os.path.abspath(filename))
        return filename

    @abc.abstractmethod
    def handle(self, data: str) -> None:
        """Save information to logging file."""

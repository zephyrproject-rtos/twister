from __future__ import annotations

import logging
from pathlib import Path

from twister2.log_file.log_file_abstract import LogFileAbstract

logger = logging.getLogger(__name__)


class BuildLogFile(LogFileAbstract):
    """Save logs from the building."""
    name = 'build'

    def __init__(self, build_dir: str | Path) -> None:
        super().__init__(build_dir=build_dir, name=self.name)

    def handle(self, data: str | bytes) -> None:
        """
        :param data: output from building
        """
        if data:
            data = data.decode(encoding=self.default_encoding) if type(data) is bytes else data
            with open(file=self.filename, mode='a+', encoding=self.default_encoding) as log_file:
                log_file.write(data)  # type: ignore
        else:
            logger.error(msg='Nothing to save into build.log.')

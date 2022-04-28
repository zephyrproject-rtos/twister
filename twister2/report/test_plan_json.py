from __future__ import annotations

import json
import logging
import os

from twister2.report.base_report_writer import BaseReportWriter

logger = logging.getLogger(__name__)


class JsonTestPlan(BaseReportWriter):
    """Write test plan as json file."""

    def __init__(self, filename: str) -> None:
        """
        :param filename: path to file where report is saved
        """
        self.filename = self._normalize_filename_path(filename)

    def write(self, data: dict) -> None:
        """
        :param data: test plan data that can be serialized to json
        """
        if not data:
            logger.warning('No data to generate test plan')
            return

        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'w', encoding='UTF-8') as fd:
            json.dump(data, fd, indent=4)

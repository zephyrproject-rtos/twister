import json
import os

from twister2.report.base_report_writer import BaseReportWriter


class JsonResultsReport(BaseReportWriter):
    """Write Json report"""

    def __init__(self, filename: str):
        self.filename = self._normalize_logfile_path(filename)

    def write(self, data: dict) -> None:
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)

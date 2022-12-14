import json
import os

from twister2.report.base_report_writer import BaseReportWriter


class JsonResultsReport(BaseReportWriter):
    """Write Json report"""

    def __init__(self, filename: str) -> None:
        """
        :param filename: path to file where report is saved
        """
        self.filename = self._normalize_filename_path(filename)

    def write(self, data: dict) -> None:
        """
        Write report data to file.

        :param data: report data that can be serialized to json
        """
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)

    def print_summary(self, terminalreporter) -> None:
        terminalreporter.write_sep('-', f'generated results report file: {self.filename}')

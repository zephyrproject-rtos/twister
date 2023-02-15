"""
Simple class to generate test plan report in CSV format
"""
import csv
import logging
import os

from twister2.report.base_report_writer import BaseReportWriter

logger = logging.getLogger(__name__)


class CsvTestPlan(BaseReportWriter):
    """Create test plan report as CSV file."""

    def __init__(self, filename: str, delimiter: str = ';', quotechar: str = '"'):
        """
        :param filename: output file name
        :param: delimiter: CSV delimiter (default: ;)
        :param quotechar: CSV quote char (default: ")
        """
        self.filename = self._normalize_filename_path(filename)
        self.delimiter = delimiter
        self.quotechar = quotechar

    def write(self, data: dict) -> None:
        """
        :param data: report data
        """
        if not data or not data.get('testsuites'):
            logger.warning('No data to generate test plan')
            return

        tests = data['testsuites']
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, 'w', encoding='UTF-8', newline='') as fd:
            fieldnames = list(tests[0].keys())
            writer = csv.DictWriter(
                fd,
                fieldnames=fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                quoting=csv.QUOTE_MINIMAL
            )
            writer.writeheader()
            writer.writerows(tests)

    def print_summary(self, terminalreporter) -> None:
        terminalreporter.write_sep('-', f'generated results report file: {self.filename}')

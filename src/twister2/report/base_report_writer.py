import abc
import os


class BaseReportWriter(abc.ABC):
    """Interface for report writer."""

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    @staticmethod
    def _normalize_filename_path(filename: str) -> str:
        filename = os.path.expanduser(os.path.expandvars(filename))
        filename = os.path.normpath(os.path.abspath(filename))
        return filename

    @abc.abstractmethod
    def write(self, data: dict) -> None:
        """Save report."""

    def print_summary(self, terminalreporter) -> None:
        terminalreporter.write_sep('-', 'Report has been written')

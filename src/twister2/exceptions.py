class TwisterException(Exception):
    """General twister exception."""


class TwisterConfigurationException(TwisterException):
    """Raised when any error appeared for plugin configuration."""


class TwisterFatalError(TwisterException):
    """Raised when Zephyr fatal error was found in parsed output from Zephyr."""


class TwisterBuildException(TwisterException):
    """Raised when any error appeared during building."""


class TwisterBuildSkipException(TwisterException):
    """Raised when test was skipped during building"""


class TwisterMemoryOverflowException(TwisterException):
    """Raised when memory overflow appeared during building."""


class TwisterFlashException(TwisterException):
    """Raised when any error appeared during flashing."""


class TwisterRunException(TwisterException):
    """Raised when any error appeared during execution."""


class TwisterTimeoutExpired(TwisterException):
    """Raised when subprocess ended due to timeout."""


class TwisterHarnessParserException(TwisterException):
    """Raised when any error appeared in Harness parser."""


class TwisterBuildFiltrationException(TwisterException):
    """Raised when Kconfig or DTS filtration should be applied for test."""

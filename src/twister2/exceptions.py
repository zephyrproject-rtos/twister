class TwisterException(Exception):
    """General twister exception."""


class TwisterConfigurationException(TwisterException):
    """Exception for all configuration errors."""


class YamlException(TwisterException):
    """Custom exception for error reporting."""


class TwisterFatalError(TwisterException):
    """Twister fatal error exception."""


class ProjectExecutionFailed(TwisterException):
    """Project execution failed exception."""


class TwisterBuildException(TwisterException):
    """Any exception during building."""


class TwisterFlashException(TwisterException):
    """Any exception during flashing."""


class TwisterRunException(TwisterException):
    """Any exception during executing."""


class TwisterTimeoutExpired(TwisterException):
    """Subprocess ended due to timeout."""


class TwisterHarnessParserException(TwisterException):
    """Harness parser exception."""

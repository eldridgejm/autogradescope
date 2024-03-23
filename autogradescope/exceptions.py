class Error(Exception):
    """Base class for all exceptions in this package."""


class TimeoutError(Error):
    """Raised when something just takes too long."""


class DoctestError(Error):
    """Raised when doctests fail."""


class SettingsError(Error):
    """Raised when there is an error in the settings."""

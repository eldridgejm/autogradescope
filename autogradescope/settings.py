"""An object to store settings for the autograder."""

from .exceptions import SettingsError


class Settings:
    """An object to store settings for the autograder.

    This object does error checking on the settings to ensure that they are
    valid, and to prevent typos from causing terrible catastrophes that could
    result, like students seeing the private tests before the due date.

    Attributes
    ----------

    default_visibility : str
        The default visibility of the tests. Valid options are:

        - "hidden": The test results are never visible to the students.

        - "visible": The test results are always visible to the students.

        - "after_published": test case will be shown only when the assignment
          is explicitly published from the "Review Grades" page.

        - "after_due_date": test case will be shown after the assignment's due
          date has passed. If late submission is allowed, then test will be
          shown only after the late due date.

    default_weight : int
        The default weight of the tests.

    default_timeout : int
        The default timeout for the tests.

    leaderboard : Optional[dict]
        A dictionary mapping leaderboard categories to scores for this
        submission. If None, no leaderboard will be used.

    failure_message : Optional[Callable]
        A function that formats a failure message for a test. If None, a
        default failure message will be used.

    """

    def __init__(
        self,
        default_visibility="after_published",
        default_weight=1,
        default_timeout=None,
        leaderboard=None,
        failure_message=None,
    ):
        self.default_visibility = default_visibility
        self.default_weight = default_weight
        self.default_timeout = default_timeout
        self.leaderboard = leaderboard
        self.failure_message = failure_message

    def _set_default_visibility(self, value):
        if value not in {
            "hidden",
            "after_due_date",
            "after_published",
            "visible",
        }:
            raise SettingsError(
                "default_visibility must be one of 'before_due_date', 'after_due_date', 'after_published', or 'visible'"
            )
        else:
            self.__dict__["default_visibility"] = value
            return

    def __setattr__(self, name, value):
        if name == "default_visibility":
            self._set_default_visibility(value)
        elif name in {
            "default_weight",
            "default_timeout",
            "leaderboard",
            "failure_message",
        }:
            self.__dict__[name] = value
        else:
            raise SettingsError(f'Configuration has no attribute "{name}".')

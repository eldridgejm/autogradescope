from .exceptions import SettingsError


class Settings:
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

from autogradescope import Settings
from autogradescope.exceptions import SettingsError

from pytest import raises


def test_checks_visibility_is_valid():
    settings = Settings()

    with raises(SettingsError):
        settings.default_visibility = "invalid"


def test_raises_when_invalid_attribute_is_set():
    settings = Settings()

    with raises(SettingsError):
        settings.invalid = "invalid"

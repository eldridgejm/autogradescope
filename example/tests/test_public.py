"""Public autograder tests."""

from autogradescope import Settings
from autogradescope.decorators import weight, timeout, visibility

# settings =============================================================================

SETTINGS = Settings()

# default_visibility -------------------------------------------------------------------
# This controls the default visibility of the tests. Valid options are:
#
# - "hidden": The test results are never visible to the students.
#
# - "visible": The test results are always visible to the students.
#
# - "after_published": test case will be shown only when the assignment is
#   explicitly published from the "Review Grades" page.
#
# - "after_due_date": test case will be shown after the assignment's due date
#   has passed. If late submission is allowed, then test will be shown only after
#   the late due date.
SETTINGS.default_visibility = "visible"

# default_weight -----------------------------------------------------------------------
# The number of points each test is worth by default.
SETTINGS.default_weight = 1

# default_timeout ----------------------------------------------------------------------
# The number of seconds before a test times out and no points are awarded.
SETTINGS.default_timeout = 60

# leaderboard --------------------------------------------------------------------------
# A dictionary mapping leaderboard categories to scores for this submission. If
# a leaderboard is used, it can be set to an empty dictionary here, and filled in with
# values in the test functions.
# SETTINGS.leaderboard = {}

# tests ================================================================================

# import student submission
import foo


def test_for_smoke():
    """Checks that your code runs without error."""
    foo.double(5)


def test_simple_1():
    """Checks that 1 doubled is 2."""
    assert foo.double(1) == 2


@weight(2)
def test_simple_2():
    """Checks that 1 doubled twice is 4."""
    assert foo.double(foo.double(1)) == 4

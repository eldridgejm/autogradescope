"""A pytest plugin that writes test output to JSON for Gradescope.

The output format required by Gradescope is described here:

    https://gradescope-autograders.readthedocs.io/en/latest/specs/

Background
==========

This plugin works by hooking into pytest at various stages of the test run. The
culminating hook is pytest_sessionfinish, which writes the test results to the
`results.json` file. The results for each test are packaged in a dictionary
created using the `summarize_test_result` helper function.

Perhaps most important is how different types of errors and failures are handled.
A technique used throughout this module is to catch certain types of fatal errors
and store them in the `.fatal_exception` attribute of the session object. Upon
session end, the presence of this attribute is checked, and if it is present, an
error message is written to `results.json` instead of the test results.

Missing/Incorrect Settings
--------------------------

Each test module must have a `SETTINGS` object; if this object is missing or if a
`SettingsError` is raised, the autograder will not run any tests, and `results.json`
will contain a single error message saying that the autograder is misconfigured.
This error is caught in the `pytest_collection_modifyitems` hook.

Timeouts
--------

Timeouts are managed in the `pytest_runtest_call` hook. If a test times out, an exception
is logged for that test, and the test is considered to have failed. However, other
tests will still run.

Incorrect Submission Name and Import Errors
-------------------------------------------

If there is an error importing a test module, the error is caught in the
`pytest_pycollect_makemodule` hook. This error is usually due to the student's
submission being named incorrectly or importing a module that doesn't exist on
Gradescope. If this happens, `results.json` will contain an error message describing
the problem, and no tests will be run.

"""

import json
import textwrap
import typing

import pytest

from . import _timeout
from . import exceptions


# helper functions =====================================================================


def remove_decorators(traceback_lines: typing.List[str]) -> typing.List[str]:
    """Removes decorators from a list containing the source code of a function."""
    if not traceback_lines:
        return []

    i = 0
    while i < len(traceback_lines) and traceback_lines[i].lstrip().startswith("@"):
        i += 1

    return traceback_lines[i:]


def format_failure_message_for_student(report, exception: Exception) -> str:
    """Formats a nice failure message containing the test code causing the failure."""
    # we show the traceback by default, unless the error is due to a failing doctest
    show_traceback = True

    if isinstance(exception, AssertionError):
        # the test failed because its output was not correct
        intro_msg = "Your code produced an incorrect output."
    elif isinstance(exception, exceptions.Error):
        # this is a autogradescope error raised, e.g., by a timeout
        intro_msg = str(exception)
        if isinstance(exception, exceptions.DoctestError):
            show_traceback = False

    elif isinstance(exception, ModuleNotFoundError):
        # the test failed because it imported some module that doesn't exist
        intro_msg = (
            f"It looks like your code is trying to import '{exception.name}', but this "
            "package does not exist on Gradescope."
        )
    else:
        # the submission raised an unexpected error
        intro_msg = f"Your code unexpectedly raised {repr(exception)}."

    intro_msg = textwrap.fill(intro_msg, 80)

    if show_traceback:
        traceback_lines: typing.List[str] = (
            report.longrepr.chain[0][0].reprentries[0].lines
        )
        traceback_lines = remove_decorators(traceback_lines)
        traceback = "\n".join(traceback_lines)
        traceback_msg = textwrap.indent(traceback, "    ")
        traceback_msg = "Here is the test that elicited the error:\n\n" + traceback_msg
    else:
        traceback_msg = ""

    return intro_msg + "\n\n" + traceback_msg


def infer_test_name(function: typing.Callable) -> str:
    """Infers the test name.

    If the function has a docstring, the first line of the docstring is used as the test
    name. Otherwise, the function name is used.

    """
    if function.__doc__ is not None:
        lines = function.__doc__.split("\n")
        return lines[0]
    else:
        return function.__name__


def output_collection_error():
    """Writes an error message to results.json when there is a collection error."""
    msg = (
        "The autograder ran into a problem when starting. This usually happens for "
        "one of two reasons: "
        "1) Your submission is incorrectly named (check the spelling); "
        "2) Your code is importing a module which does not exist on Gradescope. "
        "The exact cause can be determined by carefully reading the full error message"
        " shown above."
    )

    results_json = {"score": 0, "stdout_visibility": "visible", "output": msg}

    with open("results.json", "w") as fileobj:
        json.dump(results_json, fileobj)


def output_settings_error(session):
    """Writes an error message to results.json when there is a settings error."""
    msg = (
        "The autograder appears to be misconfigured. Contact the instructor to let them"
        " know about this problem. The full error message is shown below.\n\n"
        f"{str(session.fatal_exception)}"
    )

    results_json = {"score": 0, "stdout_visibility": "visible", "output": msg}
    with open("results.json", "w") as fileobj:
        json.dump(results_json, fileobj)


def output_no_tests_error():
    """Writes an error message to results.json when there are no tests to run."""
    msg = (
        "The autograder did not find any tests to run. This usually happens when the "
        "test module is missing or the module is empty."
    )

    results_json = {"score": 0, "stdout_visibility": "visible", "output": msg}
    with open("results.json", "w") as fileobj:
        json.dump(results_json, fileobj)


def summarize_test_result(item, report, exception: Exception):
    """Summarizes test result as a dictionary in the format expected by Gradescope."""

    settings = item.function.__globals__["SETTINGS"]

    visibility = getattr(
        item.function, "gradescope_visibility", settings.default_visibility
    )
    weight = getattr(item.function, "gradescope_weight", settings.default_weight)
    score = 0 if report.failed else weight

    test_name = infer_test_name(item.function)

    output_msg = (
        format_failure_message_for_student(report, exception) if report.failed else ""
    )
    # allow test code to override output
    if settings.failure_message is not None:
        output_msg = settings.failure_message(item, report, exception, output_msg)

    is_extra_credit = getattr(item.function, "gradescope_extra_credit", False)

    return {
        "output": output_msg,
        "visibility": visibility,
        "max_score": weight if not is_extra_credit else 0,
        "score": score,
        "name": test_name,
    }


# pytest hooks =========================================================================

# theses hooks are called by pytest at various points during the test run. they appear
# below in the order they are called.


def pytest_sessionstart(session):
    """Set up dictionary to hold test reports and exceptions."""
    session.reports = {}
    session.exceptions = {}


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makemodule(path, parent):
    """Sets session.fatal_exception if there is a problem loading a test module/plugin.

    Such a problem may be due to student submission being named incorrectly.

    """
    result = yield
    collector = result.get_result()

    # try to import the module and see what happens...
    try:
        collector.module
    except Exception as exc:
        collector.session.fatal_exception = exc


def pytest_collection_modifyitems(config, items):
    """Check that SETTINGS is present in the test module."""
    for item in items:
        if "SETTINGS" not in item.function.__globals__:
            msg = "Test module is missing SETTINGS."
            item.session.shouldstop = msg
            item.session.fatal_exception = exceptions.SettingsError(msg)
            return


def pytest_runtest_call(item):
    """When a test is run, save any exception it raises to session.exceptions.

    Note that AssertErrors arising from test failures have not been caught at this
    point, and they are saved, too.

    This is where we check for test timeouts.

    """
    settings = item.function.__globals__["SETTINGS"]

    # function-specific override
    time_limit = getattr(item.function, "gradescope_timeout", settings.default_timeout)

    time_limited_test = _timeout.timeout(time_limit)(item.runtest)

    try:
        time_limited_test()
    except Exception as exc:
        item.session.exceptions[item] = exc
        raise


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """After a test is run, save its report to session.reports."""
    result = yield
    if call.when == "call":
        report = result.get_result()
        item.session.reports[item] = report


def pytest_sessionfinish(session, exitstatus):
    """At session end, write results to Gradescope JSON."""

    # if there was a collection failure, do not write test results, but instead output
    # an error message describing the problem
    if hasattr(session, "fatal_exception"):
        if isinstance(session.fatal_exception, exceptions.SettingsError):
            # this runs when there is something wrong with the settings, such as when
            # SETTINGS is missing from the test module
            output_settings_error(session)
        else:
            # this runs when there's an import error, like when the student's submission
            # is named incorrectly, or when the student's code imports a module that
            # doesn't exist on Gradescope
            output_collection_error()
        return

    # similarly, if there are no tests to run, output an error message
    if not session.items:
        output_no_tests_error()
        return

    result_dicts = []
    for item, report in session.reports.items():
        # there is no exception if the test passed
        exception = session.exceptions.get(item, None)

        result_dict = summarize_test_result(item, report, exception)
        result_dicts.append(result_dict)

    results_json = {"tests": result_dicts}

    settings = session.items[0].function.__globals__["SETTINGS"]
    if settings.leaderboard is not None:
        results_json["leaderboard"] = [
            {"name": name, "value": value}
            for (name, value) in settings.leaderboard.items()
        ]

    with open("results.json", "w") as fileobj:
        json.dump(results_json, fileobj)

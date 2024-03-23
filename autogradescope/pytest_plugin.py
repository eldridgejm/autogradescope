"""A pytest plugin that writes easy-to-interpret test output to JSON for Gradescope."""

import json
import typing
import textwrap

import pytest

from . import _timeout
from . import exceptions


# pytest hooks
# ============


def pytest_sessionstart(session):
    """Set up a dictionary to hold test reports and exceptions at session start."""
    session.reports: typing.Dict[pytest.Item, pytest.Report] = {}
    session.exceptions: typing.Dict[pytest.Item, Exception] = {}


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "SETTINGS" not in item.function.__globals__:
            msg = "Test module is missing SETTINGS."
            item.session.shouldstop = msg
            item.session.collection_exception = exceptions.SettingsError(msg)
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
def pytest_pycollect_makemodule(path, parent):
    """Sets session.collection_exception if there is a problem loading a module.

    Such a problem may be due to student submission being named incorrectly.

    """
    result = yield
    collector = result.get_result()

    # try to import the module and see what happens...
    try:
        collector.module
    except Exception as exc:
        collector.session.collection_exception = exc


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """After a test is run, save its report to session.reports."""
    result = yield
    if call.when == "call":
        report: pytest.Report = result.get_result()
        item.session.reports[item] = report


def pytest_sessionfinish(session, exitstatus):
    """At session end, write results to Gradescope JSON with nice error messages."""

    # if there was a collection failure, we should exit immediately
    if hasattr(session, "collection_exception"):
        if isinstance(session.collection_exception, exceptions.SettingsError):
            output_configuration_error(session)
        else:
            output_collection_error(session)
        return

    result_dicts = []
    for item, report in session.reports.items():
        # there is no exception if the test passed
        exception = session.exceptions.get(item, None)

        result_dict = summarize_result(item, report, exception)
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


def output_collection_error(session):
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


def output_configuration_error(session):
    msg = (
        "The autograder appears to be misconfigured. Contact the instructor to let them"
        " know about this problem. The full error message is shown below.\n\n"
        f"{str(session.collection_exception)}"
    )

    results_json = {"score": 0, "stdout_visibility": "visible", "output": msg}
    with open("results.json", "w") as fileobj:
        json.dump(results_json, fileobj)


def summarize_result(item: pytest.Item, report, exception: Exception):
    """Summarizes test result as a dict with keys expected by Gradescope."""

    settings = item.function.__globals__["SETTINGS"]

    visibility = getattr(
        item.function, "gradescope_visibility", settings.default_visibility
    )
    weight = getattr(item.function, "gradescope_weight", settings.default_weight)
    score = 0 if report.failed else weight

    test_name = infer_test_name(item.function)

    output_msg = format_output_msg(item, report, exception) if report.failed else ""
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


def infer_test_name(function):
    """Get a test name from first line of docstring, or function name."""
    if function.__doc__ is None:
        return function.__name__
    else:
        lines = function.__doc__.split("\n")
        return lines[0]


def format_output_msg(item: pytest.Item, report, exception: Exception):
    """Formats a nice output message with the test code causing the failure."""
    # the number of frames to trim from the traceback
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
        traceback_lines = report.longrepr.chain[0][0].reprentries[0].lines
        traceback_lines = cleanup_decorators(traceback_lines)
        traceback = "\n".join(traceback_lines)
        traceback_msg = textwrap.indent(traceback, "    ")
        traceback_msg = "Here is the test that elicited the error:\n\n" + traceback_msg
    else:
        traceback_msg = ""

    return intro_msg + "\n\n" + traceback_msg


def cleanup_decorators(traceback_lines):
    """Removes leading decorators."""
    if not traceback_lines:
        return

    i = 0
    while i < len(traceback_lines) and traceback_lines[i].lstrip().startswith("@"):
        i += 1

    return traceback_lines[i:]

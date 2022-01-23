"""A pytest plugin that writes easy-to-interpret test output to JSON for Gradescope."""

import inspect
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
    session.reports: typing.Dict[pytest.Item, pytest.Report]  = {}
    session.exceptions: typing.Dict[pytest.Item, Exception] = {}


def pytest_runtest_call(item):
    """When a test is run, save any exception it raises to session.exceptions.

    Note that AssertErrors arising from test failures have not been caught at this
    point, and they are saved, too.

    This is where we check for test timeouts.

    """
    # default timeout is 60 seconds, unless overridden
    default_time_limit = item.function.__globals__.get('DEFAULT_TIMEOUT', 60)

    # function-specific override
    time_limit = getattr(item.function, 'gradescope_timeout', default_time_limit)

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
    if call.when == 'call':
        report: pytest.Report = result.get_result()
        item.session.reports[item] = report


def pytest_sessionfinish(session, exitstatus):
    """At session end, write results to Gradescope JSON with nice error messages."""

    # if there was a collection failure, we should exit immediately
    if hasattr(session, "collection_exception"):
        output_collection_error(session)
        return

    result_dicts = []
    for item, report in session.reports.items():
        # there is no exception if the test passed
        exception = session.exceptions.get(item, None)

        result_dict = summarize_result(item, report, exception)
        result_dicts.append(result_dict)

    results_json = {'tests': result_dicts}

    with open('results.json', 'w') as fileobj:
        json.dump(results_json, fileobj)


def output_collection_error(session):
    msg = textwrap.fill(
        "The autograder ran into a problem when starting. Check that your "
        "submission is correctly named.",
        80
    )

    results_json = {
        "score": 0,
        "output": msg
    }

    with open('results.json', 'w') as fileobj:
        json.dump(results_json, fileobj)


def summarize_result(item: pytest.Item, report, exception: Exception):
    """Summarizes test result as a dict with keys expected by Gradescope."""

    test_globs = item.function.__globals__
    default_weight = test_globs.get('DEFAULT_WEIGHT', 1)
    default_visibility = test_globs.get('DEFAULT_VISIBILITY', 'after_published')

    visibility = getattr(item.function, "gradescope_visibility", default_visibility)
    weight = getattr(item.function, "gradescope_weight", default_weight)
    score = 0 if report.failed else weight

    test_name = infer_test_name(item.function)

    output_msg = format_output_msg(item, report, exception) if report.failed else ''
    # allow test code to override output
    if 'autogradescope_failure_message' in test_globs:
        output_msg = test_globs['autogradescope_failure_message'](item, report, exception, output_msg)


    return {
        "output": output_msg,
        "visibility": visibility,
        "max_score": weight,
        "score": score,
        "name": test_name
    }


def infer_test_name(function):
    """Get a test name from first line of docstring, or function name."""
    if function.__doc__ is None:
        return function.__name__
    else:
        lines = function.__doc__.split('\n')
        return lines[0]


def format_output_msg(item: pytest.Item, report, exception: Exception):
    """Formats a nice output message with the test code causing the failure."""
    # the number of frames to trim from the traceback
    n_frames_to_trim = 0

    if isinstance(exception, AssertionError):
        # the test failed because its output was not correct
        intro_msg = (
            "Your code produced an incorrect output. Here is the test code that was "
            "used and the line containing the check that failed:"
        )
    elif isinstance(exception, exceptions.Error):
        # this is a autogradescope error raised, e.g., by a timeout
        intro_msg = str(exception)
        n_frames_to_trim = 1
    elif isinstance(exception, ModuleNotFoundError):
        # the test failed because it imported some module that doesn't exist
        intro_msg = (
            f"It looks like your code is trying to import '{exception.name}', but this "
            "package does not exist on Gradescope. Below is the full traceback of "
            "the error, showing where this import happened."
        )
    else:
        # the submission raised an unexpected error
        intro_msg = (
            f"Your code unexpectedly raised {repr(exception)}. Here is the full "
            "traceback showing where this exception occurred."
        )

    intro_msg = textwrap.fill(intro_msg, 80)
    traceback = trim_last_n_frames(report.longreprtext, n_frames_to_trim)
    traceback_msg = textwrap.indent(traceback, '    ')

    return intro_msg + '\n\n' + traceback_msg


def trim_last_n_frames(traceback: str, n: int):
    """Hackily hack the last n entries from the traceback string."""
    if n == 0:
        return traceback

    lines = traceback.split('\n')
    dividers = [line.strip().startswith('_ _ _ _ _') for line in lines]
    first_divider_ix = dividers.index(True)
    divider = lines[first_divider_ix]
    sections = traceback.split(divider)

    return divider.join(sections[:len(sections) - n]).strip()

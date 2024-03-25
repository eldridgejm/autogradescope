"""A convenience function for running doctests within autograder tests."""
import contextlib
import doctest
import io
import textwrap

from .exceptions import DoctestError


def run(module):
    """Runs a module's doctests.

    This can be used in autograder tests to ensure that the doctests are
    correct.

    Parameters
    ----------
    module : module
        The module to run doctests for.

    Raises
    ------
    DoctestError
        If any of the doctests fail.

    Example
    -------

    To run the doctests for a student's submission in an auto-grader test:

    .. code-block:: python

        import autogradescope.doctests

        import pp01

        def test_doctests():
            \"""Checks that the doctests pass.\"""
            autogradescope.doctests.run(pp01)

    """
    with contextlib.redirect_stdout(io.StringIO()) as f:
        result = doctest.testmod(module)

    if result.failed > 0:
        msg = textwrap.dedent(
            f"""
            Your code ran, but some of the doctests failed. Make sure to
            check the doctests by running them on your own machine.

            """.strip(
                "\n"
            )
        )

        raise DoctestError(msg)

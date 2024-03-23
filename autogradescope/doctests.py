import contextlib
import doctest
import io
import textwrap

from .exceptions import DoctestError

def run(module):
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

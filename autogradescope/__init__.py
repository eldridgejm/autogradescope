import doctest
import textwrap

from .exceptions import Error


def run_doctests(module):
    result = doctest.testmod(module)
    if result.failed > 0:
        msg = textwrap.dedent(f"""
            Your code ran, but some of the doctests failed. Make sure to
            check the doctests by running them on your own machine.
            """.strip('\n'))
        raise Error(msg)

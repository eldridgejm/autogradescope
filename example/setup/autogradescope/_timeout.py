"""Implements a simple timeout decorator using signals."""

import signal
import textwrap
from typing import Optional

from .exceptions import TimeoutError


def timeout(seconds: Optional[int]):
    """A simple timeout decorator. If seconds = None, no time limit is imposed."""
    msg = textwrap.dedent(
        f"""
        Your code took longer than {seconds} seconds to run, which is too long. We have kindly asked your code to stop running.
        """.strip(
            "\n"
        )
    )

    def _exit_test(msg: str):
        """Exits the test on timeout."""

        def handler(*args, **kwargs):
            raise TimeoutError(msg)

        return handler

    def decorator(test_function):
        def wrapped(*args, **kwargs):
            if seconds is not None:
                signal.signal(signal.SIGALRM, _exit_test(msg))
                signal.alarm(seconds)
            return test_function(*args, **kwargs)

        return wrapped

    return decorator

import signal
import textwrap

from .exceptions import TimeoutError


def timeout(seconds):
    """A simple timeout decorator. If seconds = None, no time limit is imposed."""
    msg = textwrap.dedent(
        f"""
        Your code took longer than {seconds} seconds to run, which is too long. We have kindly asked your code to stop running.
        """.strip("\n")
    )

    def decorator(test_function):
        def wrapped(*args, **kwargs):
            if seconds is not None:
                signal.signal(signal.SIGALRM, _exit_test(msg))
                signal.alarm(seconds)
            return test_function(*args, **kwargs)

        return wrapped

    return decorator


def _exit_test(msg):
    def handler(*args, **kwargs):
        raise TimeoutError(msg)

    return handler

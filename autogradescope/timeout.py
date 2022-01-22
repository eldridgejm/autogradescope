def timeout(seconds):
    """A simple timeout decorator."""
    msg = textwrap.dedent(f"""
        Your code took longer than {seconds} seconds to run, which is too long. We have kindly asked your code to stop running.
        """.strip('\n'))

    def decorator(test_function):
        def wrapped(*args, **kwargs):
            signal.signal(signal.SIGALRM, _exit_test(msg))
            signal.alarm(seconds)
            return test_function(*args, **kwargs)
        return wrapped

    return decorator


def smoke_test(test_case, name):
    """Take a glance at the submission to make sure it is reasonable.

    This will verify that the filename is correct and that all doctests pass.

    """

    if not (pathlib.Path.cwd() / (name + '.py')).exists():
        msg = textwrap.dedent(f"""
            The autograder was looking for a file named '{name}.py', but it
            does not seem to exist. Please make sure you have named your
            file correctly.
            """.strip('\n'))
        test_case.fail(msg)

    module = importlib.import_module(name)
    result = doctest.testmod(module)
    if result.failed > 0:
        msg = textwrap.dedent(f"""
            Your code ran, but some of the doctests failed. Make sure to
            check the doctests by running them on your own machine.
            """.strip('\n'))
        test_case.fail(msg)


def _exit_test(msg):
    def handler(*args, **kwargs):
        raise Exception(msg)
    return handler





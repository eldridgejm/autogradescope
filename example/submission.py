# simulated student submission
# ----------------------------


def incorrect_answer():
    return 2


def raises_exception():
    1 / 0


def imports_missing_module():
    import some_module_that_doesnt_exist


def ok():
    return 3


def doctests_ok():
    """
    >>> 2 == 2
    True
    """


def doctests_fail():
    """
    >>> 2 == 2
    False
    """


def i_take_4ever():
    while True:
        pass

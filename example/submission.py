# simulated student submission
# ----------------------------

def incorrect_answer():
    return 2

def raises_exception():
    1/0

def fails_doctests():
    """
    >>> 1 == 2
    """

def imports_missing_module():
    import some_module_that_doesnt_exist

def ok():
    return 3

def visibility(vis):
    """Changes the visibility from the default of after_published. Validates."""
    valid = {"after_due_date", "visible", "hidden", "after_published"}
    if vis not in valid:
        raise ValueError(f"Invalid visibility: {vis}. Valid options are: {valid}")

    def decorator(test_func):
        test_func.gradescope_visibility = vis
        return test_func
    return decorator


def weight(points, extra_credit=False):
    """Changes the weight from the default of 1."""
    def decorator(test_func):
        test_func.gradescope_weight = points
        test_func.gradescope_extra_credit = extra_credit
        return test_func
    return decorator

def timeout(seconds):
    """Changes the timeout from the default of 60 seconds."""
    def decorator(test_func):
        test_func.gradescope_timeout = seconds
        return test_func
    return decorator

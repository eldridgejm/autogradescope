def visibility(vis):
    """Changes the visibility from the default of after_published. Validates."""
    valid = {"after_due_date", "visible", "hidden", "after_published"}
    if vis not in valid:
        raise ValueError(f"Invalid visibility: {vis}")

    def decorator(test_func):
        test_func.gradescope_visibility = vis
        return test_func
    return decorator


def weight(points):
    """Changes the weight from the default of 1."""
    def decorator(test_func):
        test_func.gradescope_weight = points
        return test_func
    return decorator

from autogradescope.decorators import visibility, weight, timeout
from autogradescope import run_doctests

DEFAULT_VISIBILITY = 'after_due_date'
DEFAULT_WEIGHT = 2
DEFAULT_TIMEOUT = None

def autogradescope_failure_message(item, report, exc, default_msg):
    return default_msg + '\nThank you.'


import submission


# tests
# -----

@weight(2)
@visibility('visible')
def test_foo():
    """Correct answer should be 3"""
    your_answer = submission.incorrect_answer()
    assert your_answer == 3

@weight(1)
def test_your_code_imported_an_unavailable_module():
    """Does it import an unavailable module?"""
    submission.imports_missing_module()

def test_your_code_raised_an_exception():
    """Does it raise an exception"""
    submission.raises_exception()

@weight(3)
@visibility('visible')
def test_ok():
    submission.ok()

def test_doctests():
    """Run the doctests"""
    run_doctests(submission)

@timeout(3)
def test_timeout():
    """Don't timeout!"""
    submission.i_take_4ever()

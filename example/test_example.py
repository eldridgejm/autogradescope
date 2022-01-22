from autogradescope.decorators import visibility, weight
from autogradescope import run_doctests

DEFAULT_VISIBILITY = 'after_due_date'
DEFAULT_WEIGHT = 2
DEFAULT_TIMEOUT = None

def autogradescope_failure_message(item, report, exc, default_msg):
    return default_msg + '\nThank you.'


import submissionz


# tests
# -----

@weight(2)
@visibility('visible')
def test_foo():
    assert submission.incorrect_answer() == 3

@weight(1)
def test_your_code_imported_an_unavailable_module():
    submission.imports_missing_module()

def test_your_code_raised_an_exception():
    submission.raises_exception()

@weight(3)
def test_ok():
    submission.ok()

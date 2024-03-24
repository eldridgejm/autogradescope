.. autogradescope documentation master file, created by
   sphinx-quickstart on Sat Mar 16 09:49:20 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

autogradescope
==============

`autogradescope` is a Python package for creating `Gradescope
<https://www.gradescope.com>`_ autograders with `pytest
<https://docs.pytest.org/en/latest/>`_.


Getting Started
---------------

To create a new autograder, run ``python -m autogradescope`` and follow the
instructions. This will create a new directory with a template autograder. The layout
of this directory is:

.. code-block:: bash

    .
    ├── data/
    ├── setup/
    ├── solution/
    ├── tests
    │   ├── test_private.py
    │   └── test_public.py
    ├── Makefile
    └── requirements.txt

Place your public and private tests in ``tests/test_public.py`` and
``tests/test_private.py`` respectively. Put your solution code in
``solution/``, any data files that the submission will need in ``data/``, and
any requirements (e.g., `pandas`, `numpy`) in ``requirements.txt``.

Running ``make`` will test the autograder against your solution code. If all
tests pass, ``_build/autograder.zip`` will be created. This is the file that
you will upload to Gradescope.

Test File Structure
-------------------

Test files are written using `pytest`.

.. code-block:: python

    """Public autograder tests."""

    from autogradescope import Settings
    from autogradescope.decorators import weight, timeout, visibility

    # settings =============================================================================

    SETTINGS = Settings()

    # default_visibility -------------------------------------------------------------------
    # This controls the default visibility of the tests. Valid options are:
    #
    # - "hidden": The test results are never visible to the students.
    #
    # - "visible": The test results are always visible to the students.
    #
    # - "after_published": test case will be shown only when the assignment is
    #   explicitly published from the "Review Grades" page.
    #
    # - "after_due_date": test case will be shown after the assignment's due date
    #   has passed. If late submission is allowed, then test will be shown only after
    #   the late due date.
    SETTINGS.default_visibility = "visible"

    # default_weight -----------------------------------------------------------------------
    # The number of points each test is worth by default.
    SETTINGS.default_weight = 1

    # default_timeout ----------------------------------------------------------------------
    # The number of seconds before a test times out and no points are awarded.
    SETTINGS.default_timeout = 60

    # leaderboard --------------------------------------------------------------------------
    # A dictionary mapping leaderboard categories to scores for this submission. If
    # a leaderboard is used, it can be set to an empty dictionary here, and filled in with
    # values in the test functions.
    # SETTINGS.leaderboard = {}

    # tests ================================================================================

    # import the student's submission
    import submission

    def test_for_smoke():
        """Checks that the submission runs without error."""
        submission.doubler(1)

    @weight(2)
    def test_easy_1():
        """Doubling 21 makes 42."""
        assert submission.doubler(21) == 42

    @timeout(10)
    def test_lots_of_doubling():
        """Doubling 1 million gives a big number."""
        assert submission.doubler(1_000_000) == 2 * 1_000_000

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

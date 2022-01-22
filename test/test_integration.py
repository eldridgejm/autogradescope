"""These tests run pytest in the shell and look at results.json."""

import pathlib
import subprocess
import json
from textwrap import dedent

import pytest


@pytest.fixture(scope="module")
def run_example(tmpdir_factory):
    def run(script):
        # create a tempdir with test code
        test_root = pathlib.Path(tmpdir_factory.mktemp("tmp"))
        with (test_root / 'test_example.py').open('w') as fileobj:
            fileobj.write(dedent(script))

        # copy/link autogradescope into that directory
        autogradescope_path = (pathlib.Path.cwd() / '..' / 'autogradescope').resolve()
        subprocess.run(f"ln -s {autogradescope_path} {test_root}", shell=True)

        # create a stub conftest.py in that directory to load autogradescope
        with (test_root / "conftest.py").open('w') as fileobj:
            fileobj.write('pytest_plugins = "autogradescope.plugin"')

        # run the tests
        subprocess.run("pytest", cwd=test_root)

        # load and return results.json
        with (test_root / "results.json").open() as fileobj:
            return json.load(fileobj)

    return run

# decorators
# ----------

@pytest.fixture(scope="module")
def decorator_example(run_example):
    results = run_example("""
        from autogradescope.decorators import weight, visibility

        DEFAULT_WEIGHT = 3
        DEFAULT_VISIBILITY = 'after_due_date'

        @weight(2)
        def test_1():
            assert 2 == 2

        @visibility('visible')
        def test_2():
            assert 2 == 2

        @weight(3)
        @visibility('visible')
        def test_3():
            assert 2 == 2

        def test_4():
            assert 2 == 2
    """)
    return results


def test_weight_decorator_overrides(decorator_example):
    assert decorator_example['tests'][0]['score'] == 2

def test_visibility_decorator_overrides(decorator_example):
    assert decorator_example['tests'][1]['visibility'] == 'visible'

def test_weight_visibility_decorators_stack(decorator_example):
    assert decorator_example['tests'][2]['visibility'] == 'visible'
    assert decorator_example['tests'][2]['score'] == 3


# defaults
# --------

@pytest.fixture(scope="module")
def defaults_example(run_example):
    results = run_example("""
        def test_this():
            assert 2 == 2
    """)
    return results


def test_default_weight(defaults_example):
    assert defaults_example['tests'][0]['score'] == 1


def test_default_visibility(defaults_example):
    assert defaults_example['tests'][0]['visibility'] == "after_published"


@pytest.fixture(scope="module")
def overrides_example(run_example):
    results = run_example("""
        DEFAULT_WEIGHT = 2
        DEFAULT_VISIBILITY = "hidden"

        def test_this():
            assert 2 == 2
    """)
    return results


def test_default_weight_override(overrides_example):
    assert overrides_example['tests'][0]['score'] == 2


def test_default_visibility_override(overrides_example):
    assert overrides_example['tests'][0]['visibility'] == "hidden"


# scoring
# -------

def test_score_multiple_tests(run_example):
    results = run_example("""
        def test_one():
            assert 1 == 2

        def test_two():
            assert 1 == 1

        def test_three():
            assert 1 == 1

        def test_four():
            assert 1 == 3
    """)

    scores = [results['tests'][i]['score'] for i in range(4)]
    assert scores == [0, 1, 1, 0]
    assert 'score' not in results


# import_submission
# -----------------

def test_import_submission_on_missing_module(run_example):
    results = run_example("""
        import autogradescope

        submission = autogradescope.import_submission("missingmodule")
    """)

    assert results['score'] == 0
    assert 'named' in results['output']


# timeout
# -------

def test_timeout_enforced(run_example):
    results = run_example("""
        from autogradescope.decorators import timeout

        @timeout(1)
        def test_this_forever():
            while True:
                pass
    """)

    assert results['tests'][0]['score'] == 0
    assert 'too long' in results['tests'][0]['output']


def test_timeout_allows_other_tests_to_run(run_example):
    results = run_example("""
        from autogradescope.decorators import timeout

        @timeout(1)
        def test_this_forever():
            while True:
                pass

        @timeout(1)
        def test_that():
            assert 1 == 1
    """)

    assert results['tests'][1]['score'] == 1


def test_timeout_obeys_default_override(run_example):
    results = run_example("""
        from autogradescope.decorators import timeout

        DEFAULT_TIMEOUT = 1

        def test_this_forever():
            while True:
                pass

    """)

    assert results['tests'][0]['score'] == 0
    assert 'too long' in results['tests'][0]['output']


def test_test_specific_override_with_module_override(run_example):
    import time
    start = time.time()

    results = run_example("""
        from autogradescope.decorators import timeout

        DEFAULT_TIMEOUT = 20

        @timeout(1)
        def test_this_forever():
            while True:
                pass

    """)

    stop = time.time()

    assert stop - start < 2
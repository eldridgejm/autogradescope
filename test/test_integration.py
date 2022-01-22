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

def test_import_submission_on_mission_module(run_example):
    results = run_example("""
        import autogradescope

        submission = autogradescope.import_submission("missingmodule")
    """)

    assert results['score'] == 0
    assert 'failed' in results['output']

"""Integration tests for autogradescope.

These tests run pytest in the shell and check results.json to make sure it is
as expected.

"""

import pathlib
import subprocess
import json
from textwrap import dedent

import pytest


# fixtures =============================================================================


@pytest.fixture(scope="module")
def run_example(tmpdir_factory):
    """Run a test script in a temp directory and return the contents of results.json."""

    def run(script, test_root=None):
        # create a tempdir with test code
        if test_root is None:
            test_root = pathlib.Path(tmpdir_factory.mktemp("tmp"))

        with (test_root / "test_example.py").open("w") as fileobj:
            fileobj.write(dedent(script))

        # copy/link autogradescope into that directory
        autogradescope_path = (
            pathlib.Path(__file__).parent / ".." / "autogradescope"
        ).resolve()
        subprocess.run(f"cp -r {autogradescope_path} {test_root}", shell=True)

        # remove the template directory; it contains tests and will interfere with
        # pytest
        subprocess.run(f"rm -r {test_root}/autogradescope/template", shell=True)

        # create a stub conftest.py in that directory to load autogradescope
        with (test_root / "conftest.py").open("w") as fileobj:
            fileobj.write('pytest_plugins = "autogradescope.pytest_plugin"')

        # run the tests
        subprocess.run("pytest", cwd=test_root)

        # load and return results.json
        with (test_root / "results.json").open() as fileobj:
            return json.load(fileobj)

    return run


# tests ================================================================================

# collection oriented ------------------------------------------------------------------


def test_prints_a_message_if_there_are_no_tests(run_example):
    results = run_example(
        """
        from autogradescope import Settings
        SETTINGS = Settings()
    """
    )
    assert "did not find any tests" in results["output"]


# settings -------------------------------------------------------------------


def test_raises_if_there_is_no_SETTINGS_variable(run_example):
    results = run_example(
        """
        def test_one():
            assert 2 == 2
    """
    )

    assert "misconfigured" in results["output"]
    assert "missing SETTINGS" in results["output"]


def test_with_invalid_default_visibility(run_example):
    results = run_example(
        """
        from autogradescope import Settings

        SETTINGS = Settings()

        SETTINGS.default_visibility = "after_publishedz"

        def test_one():
            assert 2 == 2
    """
    )

    assert "tests" not in results
    assert "misconfigured" in results["output"]


def test_with_invalid_attribute_added_to_Settings(run_example):
    results = run_example(
        """
        from autogradescope import Settings

        SETTINGS = Settings()

        SETTINGS.nonexistant_attribute = 3

        def test_one():
            assert 2 == 2
    """
    )

    assert "tests" not in results
    assert "misconfigured" in results["output"]


def test_modifying_settings_affects_results_json(run_example):
    results = run_example(
        """
        from autogradescope import Settings

        SETTINGS = Settings()

        SETTINGS.default_weight = 3

        def test_one():
            assert 2 == 2
    """
    )

    assert results["tests"][0]["score"] == 3


@pytest.fixture(scope="module")
def defaults_example(run_example):
    results = run_example(
        """
        from autogradescope import Settings
        SETTINGS = Settings()
        def test_this():
            assert 2 == 2
    """
    )
    return results


def test_default_weight_is_one(defaults_example):
    assert defaults_example["tests"][0]["score"] == 1


def test_default_visibility_is_after_published(defaults_example):
    assert defaults_example["tests"][0]["visibility"] == "after_published"


@pytest.fixture(scope="module")
def overrides_example(run_example):
    results = run_example(
        """
        from autogradescope import Settings
        SETTINGS = Settings()
        SETTINGS.default_weight = 2
        SETTINGS.default_visibility = "hidden"

        def test_this():
            assert 2 == 2
    """
    )
    return results


def test_default_weight_override(overrides_example):
    assert overrides_example["tests"][0]["score"] == 2


def test_default_visibility_override(overrides_example):
    assert overrides_example["tests"][0]["visibility"] == "hidden"


# decorators ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def decorator_example(run_example):
    results = run_example(
        """
        from autogradescope.decorators import weight, visibility
        from autogradescope import Settings
        SETTINGS = Settings()

        SETTINGS.default_weight = 3
        SETTINGS.default_visibility = 'after_due_date'

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

        @weight(2, extra_credit=True)
        def test_5():
            assert 3 == 3

    """
    )
    return results


def test_weight_decorator_overrides(decorator_example):
    assert decorator_example["tests"][0]["score"] == 2
    assert decorator_example["tests"][0]["max_score"] == 2


def test_visibility_decorator_overrides(decorator_example):
    assert decorator_example["tests"][1]["visibility"] == "visible"


def test_weight_visibility_decorators_stack(decorator_example):
    assert decorator_example["tests"][2]["visibility"] == "visible"
    assert decorator_example["tests"][2]["score"] == 3


def test_extra_credit_decorator_sets_max_points(decorator_example):
    assert decorator_example["tests"][4]["score"] == 2
    assert decorator_example["tests"][4]["max_score"] == 0


def test_test_specific_override_with_module_override(run_example):
    import time

    start = time.time()

    results = run_example(
        """
        from autogradescope.decorators import timeout

        from autogradescope import Settings
        SETTINGS = Settings()
        SETTINGS.default_timeout = 20

        @timeout(1)
        def test_this_forever():
            while True:
                pass

    """
    )

    stop = time.time()

    assert stop - start < 2


# scoring ------------------------------------------------------------------------------


def test_score_multiple_tests(run_example):
    results = run_example(
        """
        from autogradescope import Settings
        SETTINGS = Settings()

        def test_one():
            assert 1 == 2

        def test_two():
            assert 1 == 1

        def test_three():
            assert 1 == 1

        def test_four():
            assert 1 == 3
    """
    )

    scores = [results["tests"][i]["score"] for i in range(4)]
    assert scores == [0, 1, 1, 0]
    assert "score" not in results


# missing submission / bad imports -----------------------------------------------------


def test_overall_score_zero_on_missing_imports(run_example, tmpdir_factory):
    test_root = pathlib.Path(tmpdir_factory.mktemp("tmp"))

    with (test_root / "submission.py").open("w") as fileobj:
        fileobj.write(
            dedent(
                """
            import wldakdsa

            def foo():
                return 42
            """
            )
        )

    results = run_example(
        """
        from autogradescope.decorators import timeout

        import submission

        def test_that_this_fails():
            assert submission.foo() == 42

    """,
        test_root=test_root,
    )

    assert results["score"] == 0


def test_useful_overall_error_message_on_missing_import(run_example, tmpdir_factory):
    test_root = pathlib.Path(tmpdir_factory.mktemp("tmp"))

    with (test_root / "submission.py").open("w") as fileobj:
        fileobj.write(
            dedent(
                """
            import this_module_doesnt_exist

            def foo():
                return 42
            """
            )
        )

    results = run_example(
        """
        from autogradescope.decorators import timeout

        import submission

        def test_that_this_fails():
            assert submission.foo() == 42

    """,
        test_root=test_root,
    )

    assert "code is importing a module which does not exist" in results["output"]


def test_useful_overall_error_message_on_missing_submission(run_example):
    results = run_example(
        """
        from autogradescope.decorators import timeout

        import submission

        def test_that_this_fails():
            assert submission.foo() == 42

    """
    )

    assert "submission" in results["output"]


# timeouts -----------------------------------------------------------------------------


def test_timeout_enforced(run_example):
    results = run_example(
        """
        from autogradescope.decorators import timeout
        from autogradescope import Settings

        SETTINGS = Settings()

        @timeout(1)
        def test_this_forever():
            while True:
                pass
    """
    )

    assert results["tests"][0]["score"] == 0
    assert "too long" in results["tests"][0]["output"]


def test_timeout_allows_other_tests_to_run(run_example):
    results = run_example(
        """
        from autogradescope.decorators import timeout
        from autogradescope import Settings

        SETTINGS = Settings()

        @timeout(1)
        def test_this_forever():
            while True:
                pass

        @timeout(1)
        def test_that():
            assert 1 == 1
    """
    )

    assert results["tests"][1]["score"] == 1


def test_timeout_obeys_default_override(run_example):
    results = run_example(
        """
        from autogradescope.decorators import timeout

        from autogradescope import Settings
        SETTINGS = Settings()
        SETTINGS.default_timeout = 1

        def test_this_forever():
            while True:
                pass

    """
    )

    assert results["tests"][0]["score"] == 0
    assert "too long" in results["tests"][0]["output"]


# test name inference ------------------------------------------------------------------


def test_gets_name_from_first_line_of_docstring(run_example):
    results = run_example(
        """
        from autogradescope.decorators import timeout
        from autogradescope import Settings

        SETTINGS = Settings()

        def test_that_this_fails():
            \"""This just always fails

            We hope.
            \"""
            assert 2 == 3

    """
    )

    assert results["tests"][0]["name"] == "This just always fails"


def test_gets_name_from_function_name_if_no_docstring(run_example):
    results = run_example(
        """
        from autogradescope.decorators import timeout
        from autogradescope import Settings

        SETTINGS = Settings()

        def test_that_this_fails():
            assert 2 == 3

    """
    )

    assert results["tests"][0]["name"] == "test_that_this_fails"


# leaderboard --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def leaderboard_example(run_example):
    results = run_example(
        """
        from autogradescope import Settings
        SETTINGS = Settings()
        SETTINGS.leaderboard = {}

        def test_this():
            SETTINGS.leaderboard['accuracy'] = .89
            SETTINGS.leaderboard['speed'] = .2

    """
    )
    return results


def test_leaderboard(leaderboard_example):
    assert leaderboard_example["leaderboard"][0] == {"name": "accuracy", "value": 0.89}

    assert leaderboard_example["leaderboard"][1] == {"name": "speed", "value": 0.2}


# doctests -----------------------------------------------------------------------------


def test_fails_if_doctest_fails(run_example, tmp_path_factory):
    test_root = tmp_path_factory.mktemp("tmp")

    with (test_root / "submission.py").open("w") as fileobj:
        fileobj.write(
            dedent(
                """
            def foo():
                \"""
                >>> foo() == 43
                \"""
                return 42
            """
            )
        )

    results = run_example(
        """
        from autogradescope import Settings, doctests
        SETTINGS = Settings()

        import submission

        def test_this():
            doctests.run(submission)

    """,
        test_root=test_root,
    )

    assert "some of the doctests failed" in results["tests"][0]["output"]


def test_ok_if_doctests_pass(run_example, tmp_path_factory):
    test_root = tmp_path_factory.mktemp("tmp")

    with (test_root / "submission.py").open("w") as fileobj:
        fileobj.write(
            dedent(
                """
            def foo():
                \"""
                >>> foo() == 42
                \"""
                return 42
            """
            )
        )

    results = run_example(
        """
        from autogradescope import Settings, doctests
        SETTINGS = Settings()

        import submission

        def test_this():
            doctests.run(submission)

    """,
        test_root=test_root,
    )

    assert "doctests" not in results

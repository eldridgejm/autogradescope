"""Command-line interface that creates an autograder from a template."""

import sys
import importlib.resources
import shutil
import pathlib

import click
import rich

# helper functions =====================================================================


def print_error(message):
    rich.print(f"[red]{message}[/red]")
    sys.exit(1)


def replace_line(file_path, old_line, new_line):
    """Replace a line in a file with a new line."""
    with open(file_path, "r") as fileobj:
        lines = fileobj.readlines()

    with open(file_path, "w") as fileobj:
        for line in lines:
            if line.strip() == old_line:
                fileobj.write(new_line)
            else:
                fileobj.write(line)


def copy_template(template_path, dest_path):
    """Copy the template to the destination path.

    This avoids using shutil.copytree since it doesn't work well with
    package resources (which may be read-only).
    """

    def copy_template_file(src, dest):
        with open(src, "r") as fileobj:
            content = fileobj.read()

        dest.write_text(content)

    def copy_template_directory(src, dest):
        if src.name == "__pycache__":
            return

        dest.mkdir()
        for item in src.iterdir():
            if item.is_dir():
                copy_template_directory(item, dest / item.name)
            else:
                copy_template_file(item, dest / item.name)

    copy_template_directory(template_path, dest_path)

# main function =====================================================================


@click.command()
def main():
    """Creates an autograder for Gradescope from a template."""
    if pathlib.Path("autograder").exists():
        print_error("Directory 'autograder' already exists")

    # ask for the module name
    module_name = click.prompt("Name of the module submitted by students", type=str)

    print("Creating autograder...")

    # copy the template
    template_path = importlib.resources.files("autogradescope") / "template"
    copy_template(template_path, pathlib.Path("autograder"))

    # copy the autogradescope source into the autograder setup
    src_path = importlib.resources.files("autogradescope")
    copy_template(src_path, pathlib.Path("autograder/setup/autogradescope"))

    # remove the autogradescope/template directory
    shutil.rmtree("autograder/setup/autogradescope/template")

    # remove any __pycache__ directories
    for pycache in pathlib.Path("autograder").rglob("__pycache__"):
        shutil.rmtree(pycache)

    # replace the '# import submission' line in the test files with the actual module name
    msg = "# import student submission"
    replace_line(
        "autograder/tests/test_public.py",
        "# import submission",
        f"{msg}\nimport {module_name}",
    )
    replace_line(
        "autograder/tests/test_private.py",
        "# import submission",
        f"{msg}\nimport {module_name}",
    )

    # create the solution module
    solution_module_path = pathlib.Path(f"autograder/solution/{module_name}.py")
    solution_module_path.touch()

if __name__ == "__main__":
    main()

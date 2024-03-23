import sys
import importlib.resources
import shutil
import pathlib

import click
import rich


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


@click.command()
def main():
    if pathlib.Path("foo").exists():
        print_error("Directory 'foo' already exists")

    # ask for the module name
    module_name = click.prompt("Name of the module submitted by students", type=str)

    print("Creating autograder...")

    # copy the template
    template_path = importlib.resources.files("autogradescope") / "template"
    shutil.copytree(template_path, "foo")

    # copy the autogradescope source into the autograder setup
    src_path = importlib.resources.files("autogradescope")
    shutil.copytree(src_path, "foo/setup/autogradescope")

    # remove the autogradescope/template directory
    shutil.rmtree("foo/setup/autogradescope/template")

    # remove any __pycache__ directories
    for pycache in pathlib.Path("foo").rglob("__pycache__"):
        shutil.rmtree(pycache)

    # replace the '# import submission' line in the test files with the actual module name
    msg = "# import student submission"
    replace_line(
        "foo/tests/test_public.py", "# import submission", f"{msg}\nimport {module_name}"
    )
    replace_line(
        "foo/tests/test_private.py", "# import submission", f"{msg}\nimport {module_name}"
    )

    rich.print("[green]Autograder created successfully![/green]")


if __name__ == "__main__":
    main()

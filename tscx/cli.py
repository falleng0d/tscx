import os
import re
import shutil
import subprocess
import sys
from subprocess import CompletedProcess

import click


def is_command_available(command: str) -> bool:
    """Check if a command is available in the PATH."""
    return shutil.which(command) is not None


@click.group(invoke_without_command=True)
@click.version_option()
@click.argument("files", nargs=-1, required=False)
@click.option(
    "-p",
    "--project",
    default=".",
    help="Path to the TypeScript project (default: current directory)",
)
@click.option(
    "--tsc-path",
    default="node_modules/.bin/tsc",
    help="Path to TypeScript compiler (default: node_modules/.bin/tsc)",
)
@click.pass_context
def cli(ctx: click.Context, files: tuple[str, ...], project: str, tsc_path: str):
    """Runs TypeScript type checking and filters the results to show only errors from
    specific files.

    Provide one or more file paths as arguments to filter TypeScript errors for only
    those files. If no files are provided, all errors will be shown.
    """
    # If no subcommand is invoked, run the main functionality
    if ctx.invoked_subcommand is None:
        exit_code = run_tsc_for_file(files, project, tsc_path)
        sys.exit(exit_code)


def execute_tsc(tsc_path: str, project: str) -> tuple[CompletedProcess | None, int]:
    """Execute TypeScript compiler and return the result.

    Args:
        tsc_path: Path to the TypeScript compiler executable
        project: Path to the TypeScript project

    Returns:
        Tuple containing the subprocess result and an exit code
        (0 for success, 1 for error)
    """
    # If the specified path is the default local one, and it doesn't exist,
    # try using the global 'tsc' command
    if tsc_path == "node_modules/.bin/tsc" and not os.path.exists(tsc_path):
        tsc_path = "tsc"

    # Run TypeScript compiler
    try:
        result = subprocess.run(
            [tsc_path, "--noEmit", "-p", project],
            check=False,
            capture_output=True,
            text=True,
        )
        return result, 0
    except Exception as e:
        click.echo(f"Error running TypeScript compiler: {str(e)}", err=True)
        return None, 1


def run_tsc_for_file(files: tuple[str, ...], project: str, tsc_path: str) -> int:
    """Run TypeScript compiler and filter results.

    Args:
        files: Tuple of file paths to filter errors for
        project: Path to the TypeScript project
        tsc_path: Path to the TypeScript compiler executable

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    # Create a dictionary of files to include
    include_files: dict[str, int] = {}
    pwd = os.getcwd()

    for f in files:
        if f.startswith(pwd):
            key = f[len(pwd) + 1 :] if f.startswith(pwd + os.sep) else f[len(pwd) :]
        else:
            key = f
        include_files[key] = 1

    # Execute TypeScript compiler
    result, status = execute_tsc(tsc_path, project)
    if status != 0 or result is None:
        return status

    status = 0
    show_continuation = False

    # If no files specified, show all output
    show_all = len(include_files) == 0

    # Process each line of output
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        if line.startswith(" "):
            # This is a continuation line
            if show_continuation or show_all:
                click.echo(line, err=True)
        else:
            # This is a new error message - extract the filename
            file_match = re.match(r"^([^(]+)", line)
            if file_match:
                file = file_match.group(1).strip()
                if file in include_files or show_all:
                    show_continuation = True
                    click.echo(line, err=True)
                    status = 1
                else:
                    show_continuation = False

    return status


@cli.command(name="check")
@click.argument("files", nargs=-1, required=False)
@click.option(
    "-p",
    "--project",
    default=".",
    help="Path to the TypeScript project (default: current directory)",
)
@click.option(
    "--tsc-path",
    default="node_modules/.bin/tsc",
    help="Path to TypeScript compiler (default: node_modules/.bin/tsc)",
)
def check_command(files: tuple[str, ...], project: str, tsc_path: str) -> int:
    """Alternative command to run TypeScript type checking.

    This is an alternative to the main command and works the same way.
    """
    return run_tsc_for_file(files, project, tsc_path)

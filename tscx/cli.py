import os
import re
import shutil
import subprocess
import sys
from subprocess import CompletedProcess

import click


def strip_ansi_escape_sequences(text: str) -> str:
    """Remove ANSI escape sequences from a string.

    This is used to clean terminal color codes and other escape sequences
    from the output of commands that use --pretty or similar flags.

    Args:
        text: The string containing ANSI escape sequences

    Returns:
        The string with all ANSI escape sequences removed
    """
    # This pattern matches all ANSI escape sequences
    # including color codes and cursor movement commands
    ansi_escape_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape_pattern.sub("", text)


def is_command_available(command: str) -> bool:
    """Check if a command is available in the PATH."""
    return shutil.which(command) is not None


@click.group(invoke_without_command=True)
@click.version_option()
@click.argument("files", nargs=-1, required=False)
@click.option(
    "-p",
    "--project",
    default=None,
    help="Path to the TypeScript project (default: no project)",
)
@click.option(
    "--tsc-path",
    default=None,
    help="Path to TypeScript compiler (default: no custom path)",
)
@click.pass_context
def cli(
    ctx: click.Context, files: tuple[str, ...], project: str | None, tsc_path: str | None
):
    """Runs TypeScript type checking and filters the results to show only errors from
    specific files.

    Provide one or more file paths as arguments to filter TypeScript errors for only
    those files. If no files are provided, all errors will be shown.
    """
    # If no subcommand is invoked, run the main functionality
    if ctx.invoked_subcommand is None:
        exit_code = run_tsc_for_file(files, project, tsc_path)
        sys.exit(exit_code)


def execute_tsc(
    tsc_path: str | None, project: str | None
) -> tuple[CompletedProcess | None, int]:
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
    if tsc_path and not os.path.exists(tsc_path) or not tsc_path:
        tsc_path = "tsc"

    # Run TypeScript compiler
    try:
        args = (
            [tsc_path, "--noEmit", "--pretty", "-p", project]
            if project
            else [tsc_path, "--noEmit", "--pretty"]
        )
        if os.name == "nt":
            args[0] = f"{args[0]}.cmd"

        print(f"Running TypeScript compiler: {' '.join(args)}")

        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
        )
        return result, 0
    except Exception as e:
        click.echo(f"Error running TypeScript compiler: {str(e)}", err=True)
        return None, 1


def run_tsc_for_file(files: tuple[str, ...], project: str | None, tsc_path: str | None):
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
    show_all = not include_files

    # Process each line of output
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        # First, sanitize the line to check if it's a continuation line
        # but keep the original line for display
        sanitized_line = strip_ansi_escape_sequences(line)

        if (
            sanitized_line.startswith(" ")
            or re.match(r"^\d+\s+", sanitized_line) is not None
        ):
            # This is a continuation line
            if show_continuation or show_all:
                click.echo(line, err=True)
        elif file_match := re.match(r"^([^:(]+)", sanitized_line):
            file_path = file_match[1].strip()
            file_name = os.path.basename(file_path)
            if file_name in include_files or show_all:
                show_continuation = True
                click.echo(line, err=True)  # Echo the original line with colors
                status = 1
            else:
                show_continuation = False

    return status


@cli.command(name="check")
@click.argument("files", nargs=-1, required=False)
@click.option(
    "-p",
    "--project",
    default=None,
    help="Path to the TypeScript project (default: no project)",
)
@click.option(
    "--tsc-path",
    default=None,
    help="Path to TypeScript compiler (default: no custom path)",
)
def check_command(files: tuple[str, ...], project: str | None, tsc_path: str | None):
    """Alternative command to run TypeScript type checking.

    This is an alternative to the main command and works the same way.
    """
    return run_tsc_for_file(files, project, tsc_path)

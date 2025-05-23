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
@click.argument("paths", nargs=-1, required=False)
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
@click.option(
    "--pretty",
    is_flag=True,
    default=False,
    help="Use --pretty flag for formatted TypeScript compiler output",
)
@click.pass_context
def cli(
    ctx: click.Context,
    paths: tuple[str, ...],
    project: str | None,
    tsc_path: str | None,
    pretty: bool,
):
    """Runs TypeScript type checking and filters the results to show only errors from
    specific files or directories.

    Provide one or more file paths or directory paths as arguments to filter TypeScript errors.
    If a directory path is provided, all errors from files within that directory and its
    subdirectories will be shown. If no paths are provided, all errors will be shown.
    """
    # If no subcommand is invoked, run the main functionality
    if ctx.invoked_subcommand is None:
        exit_code = run_tsc_for_file(paths, project, tsc_path, pretty)
        sys.exit(exit_code)


def _execute_tsc_with_parameters(tsc_path, pretty, project):
    base_args = [tsc_path, "--noEmit"]
    if pretty:
        base_args.append("--pretty")

    args = base_args + ["-p", project] if project else base_args

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


def execute_tsc(
    tsc_path: str | None, project: str | None, pretty: bool = False
) -> tuple[CompletedProcess | None, int]:
    """Execute TypeScript compiler and return the result.

    Args:
        tsc_path: Path to the TypeScript compiler executable
        project: Path to the TypeScript project
        pretty: Whether to use the --pretty flag for formatted output

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
        return _execute_tsc_with_parameters(tsc_path, pretty, project)
    except Exception as e:
        click.echo(f"Error running TypeScript compiler: {str(e)}", err=True)
        return None, 1


def run_tsc_for_file(
    files: tuple[str, ...],
    project: str | None,
    tsc_path: str | None,
    pretty: bool = False,
):
    """Run TypeScript compiler and filter results.

    Args:
        files: Tuple of file paths or directory paths to filter errors for.
               If a directory path is provided, all files within that directory
               and its subdirectories will be included in the filtering.
        project: Path to the TypeScript project
        tsc_path: Path to the TypeScript compiler executable
        pretty: Whether to use the --pretty flag for formatted output

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    include_files: dict[str, int] = {}
    include_paths: list[str] = []
    pwd = os.getcwd()

    for f in files:
        # Normalize the path relative to current working directory
        if f.startswith(pwd):
            key = f[len(pwd) + 1 :] if f.startswith(pwd + os.sep) else f[len(pwd) :]
        else:
            key = f

        if os.path.isdir(f):
            include_paths.append(key)
        else:
            include_files[key] = 1

    result, status = execute_tsc(tsc_path, project, pretty)
    if status != 0 or result is None:
        return status

    status = 0
    show_continuation = False

    show_all = not include_files and not include_paths

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

            # Check if the file is in any of the specified directories
            in_specified_path = False
            if include_paths:
                for path in include_paths:
                    # Check if file_path starts with or contains the specified path
                    if file_path.startswith(path) or f"/{path}/" in f"/{file_path}/":
                        in_specified_path = True
                        break

            # Show the line if:
            # 1. The file name matches one of the specified files, or
            # 2. The file is in one of the specified directories, or
            # 3. No filters were specified (show all)
            if file_name in include_files or in_specified_path or show_all:
                show_continuation = True
                click.echo(line, err=True)  # Echo the original line with colors
                status = 1
            else:
                show_continuation = False

    return status


@cli.command(name="check")
@click.argument("paths", nargs=-1, required=False)
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
@click.option(
    "--pretty",
    is_flag=True,
    default=False,
    help="Use --pretty flag for formatted TypeScript compiler output",
)
def check_command(
    paths: tuple[str, ...],
    project: str | None,
    tsc_path: str | None,
    pretty: bool = False,
):
    """Alternative command"""
    return run_tsc_for_file(paths, project, tsc_path, pretty)

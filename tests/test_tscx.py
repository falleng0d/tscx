import subprocess
from unittest import mock

from click.testing import CliRunner

from tscx.cli import cli


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


@mock.patch("os.path.exists")
@mock.patch("subprocess.run")
def test_tsc_not_found(mock_run, mock_exists):
    # Mock os.path.exists to return False
    mock_exists.return_value = False
    # Mock subprocess.run to raise FileNotFoundError
    mock_run.side_effect = FileNotFoundError()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli)
        assert result.exit_code == 1
        assert "Error running TypeScript compiler" in result.stderr


@mock.patch("os.path.exists")
@mock.patch("subprocess.run")
def test_tsc_no_errors(mock_run, mock_exists):
    mock_exists.return_value = True

    mock_process = subprocess.CompletedProcess(
        args=["tsc", "--noEmit"],
        returncode=0,
        stdout="",
        stderr="",
    )
    mock_run.return_value = mock_process

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Test without pretty flag
        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert result.stderr == ""


@mock.patch("os.path.exists")
@mock.patch("subprocess.run")
def test_tsc_no_errors_pretty(mock_run, mock_exists):
    mock_exists.return_value = True

    mock_process = subprocess.CompletedProcess(
        args=["tsc", "--noEmit", "--pretty"],
        returncode=0,
        stdout="",
        stderr="",
    )
    mock_run.return_value = mock_process

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Test with pretty flag
        result = runner.invoke(cli, ["--pretty"])
        assert result.exit_code == 0
        assert result.stderr == ""


@mock.patch("os.path.exists")
@mock.patch("subprocess.run")
def test_tsc_with_errors(mock_run, mock_exists):
    mock_exists.return_value = True

    mock_stdout = (
        "src/file1.ts(10,12): error TS2322: Type 'string' is not assignable to type 'number'.\n"
        "  This is a continuation line\n"
        "src/file2.ts(20,5): error TS2345: Argument of type 'string' is not assignable to parameter of type 'boolean'.\n"
    )

    mock_process = subprocess.CompletedProcess(
        args=["tsc", "--noEmit"],
        returncode=1,
        stdout=mock_stdout,
        stderr="",
    )

    mock_run.return_value = mock_process

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Test with no file filter (should show all errors)
        result = runner.invoke(cli)
        assert result.exit_code == 1
        assert "src/file1.ts" in result.stderr
        assert "src/file2.ts" in result.stderr
        assert "This is a continuation line" in result.stderr


@mock.patch("os.path.exists")
@mock.patch("subprocess.run")
def test_tsc_with_errors_file_filter(mock_run, mock_exists):
    mock_exists.return_value = True

    mock_stdout = (
        "src/file1.ts(10,12): error TS2322: Type 'string' is not assignable to type 'number'.\n"
        "  This is a continuation line\n"
        "src/file2.ts(20,5): error TS2345: Argument of type 'string' is not assignable to parameter of type 'boolean'.\n"
    )

    mock_process = subprocess.CompletedProcess(
        args=["tsc", "--noEmit"],
        returncode=1,
        stdout=mock_stdout,
        stderr="",
    )

    mock_run.return_value = mock_process

    # Create a file in the filesystem to match our filter
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a file that matches the filter
        with open("file1.ts", "w") as f:
            f.write("// Test file")

        # Test with file filter (should only show errors for file1)
        result = runner.invoke(cli, ["file1.ts"])
        assert result.exit_code == 1
        assert "src/file1.ts" in result.stderr
        assert "This is a continuation line" in result.stderr
        assert "src/file2.ts" not in result.stderr


@mock.patch("os.path.exists")
@mock.patch("subprocess.run")
def test_tsc_with_errors_pretty(mock_run, mock_exists):
    mock_exists.return_value = True

    mock_stdout = (
        "src/file1.ts(10,12): error TS2322: Type 'string' is not assignable to type 'number'.\n"
        "  This is a continuation line\n"
        "src/file2.ts(20,5): error TS2345: Argument of type 'string' is not assignable to parameter of type 'boolean'.\n"
    )

    mock_process = subprocess.CompletedProcess(
        args=["tsc", "--noEmit", "--pretty"],
        returncode=1,
        stdout=mock_stdout,
        stderr="",
    )

    mock_run.return_value = mock_process

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Test with pretty flag
        result = runner.invoke(cli, ["--pretty"])
        assert result.exit_code == 1
        assert "src/file1.ts" in result.stderr
        assert "src/file2.ts" in result.stderr


@mock.patch("os.path.exists")
@mock.patch("os.path.isdir")
@mock.patch("subprocess.run")
def test_tsc_with_errors_directory_filter(mock_run, mock_isdir, mock_exists):
    mock_exists.return_value = True

    # Configure mock_isdir to return True for directories and False for files
    def is_directory(path):
        return path == "src"

    mock_isdir.side_effect = is_directory

    mock_stdout = (
        "src/file1.ts(10,12): error TS2322: Type 'string' is not assignable to type 'number'.\n"
        "  This is a continuation line\n"
        "src/file2.ts(20,5): error TS2345: Argument of type 'string' is not assignable to parameter of type 'boolean'.\n"
        "lib/utils.ts(15,3): error TS2551: Property 'foo' does not exist on type 'UtilProps'.\n"
    )

    mock_process = subprocess.CompletedProcess(
        args=["tsc", "--noEmit"],
        returncode=1,
        stdout=mock_stdout,
        stderr="",
    )

    mock_run.return_value = mock_process

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a directory that matches the filter
        import os
        os.makedirs("src", exist_ok=True)

        # Test with directory filter (should only show errors for files in src/)
        result = runner.invoke(cli, ["src"])
        assert result.exit_code == 1
        assert "src/file1.ts" in result.stderr
        assert "src/file2.ts" in result.stderr
        assert "This is a continuation line" in result.stderr
        assert "lib/utils.ts" not in result.stderr

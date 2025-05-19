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
    # Mock os.path.exists to return True for tsc
    mock_exists.return_value = True

    # Mock subprocess.run to return a CompletedProcess with no output
    mock_process = subprocess.CompletedProcess(
        args=["node_modules/.bin/tsc", "--noEmit", "-p", "."],
        returncode=0,
        stdout="",
        stderr="",
    )
    mock_run.return_value = mock_process

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert result.stderr == ""


@mock.patch("os.path.exists")
@mock.patch("subprocess.run")
def test_tsc_with_errors(mock_run, mock_exists):
    # Mock os.path.exists to return True for tsc
    mock_exists.return_value = True

    # Mock subprocess.run to return a CompletedProcess with TypeScript errors
    mock_stdout = (
        "src/file1.ts(10,12): error TS2322: Type 'string' is not assignable to type 'number'.\n"
        "  This is a continuation line\n"
        "src/file2.ts(20,5): error TS2345: Argument of type 'string' is not assignable to parameter of type 'boolean'.\n"
    )
    mock_process = subprocess.CompletedProcess(
        args=["node_modules/.bin/tsc", "--noEmit", "-p", "."],
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

        # Test with file filter (should only show errors for file1)
        result = runner.invoke(cli, ["src/file1.ts"])
        assert result.exit_code == 1
        assert "src/file1.ts" in result.stderr
        assert "This is a continuation line" in result.stderr
        assert "src/file2.ts" not in result.stderr

# tscx

[![PyPI](https://img.shields.io/pypi/v/tscx.svg)](https://pypi.org/project/tscx/)
[![Changelog](https://img.shields.io/github/v/release/falleng0d/tscx?include_prereleases&label=changelog)](https://github.com/falleng0d/tscx/releases)
[![Tests](https://github.com/falleng0d/tscx/actions/workflows/test.yml/badge.svg)](https://github.com/falleng0d/tscx/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/falleng0d/tscx/blob/master/LICENSE)

Runs TypeScript type checking and filters the results to show only errors from specific files.

## Installation

Install this tool using `pip`:
```bash
pip install tscx
```

## Usage

### Basic Usage

Run TypeScript type checking and show all errors:
```bash
tscx
```

Filter errors for specific files:
```bash
tscx path/to/file1.ts path/to/file2.ts
```

Filter errors for files in specific directories:
```bash
tscx src/components src/utils
```

### Options

- `-p, --project PATH`: Specify the TypeScript project path (default: current directory)
- `--tsc-path PATH`: Specify the path to TypeScript compiler (default: node_modules/.bin/tsc)

> **Note:** If the TypeScript compiler is not found at the default path (`node_modules/.bin/tsc`), the tool will automatically try to use the global `tsc` command.

### Examples

Check a specific project:
```bash
tscx -p ./my-ts-project
```

Use a custom TypeScript compiler path:
```bash
tscx --tsc-path /custom/path/to/tsc
```

Filter errors for specific files in a project:
```bash
tscx -p ./my-ts-project src/components/Button.tsx src/utils/helpers.ts
```

Filter errors for all files in specific directories:
```bash
tscx -p ./my-ts-project src/components src/utils
```

For help, run:
```bash
tscx --help
```

You can also use:
```bash
python -m tscx --help
```
## Development

### Using UV (Recommended)

To contribute to this tool using UV, first checkout the code:

```bash
cd tscx
```

Use UV to set up the project and install dependencies:

```bash
uv sync
```

Run commands using UV:

```bash
# Run tests
uv run pytest

# Run the CLI tool
uv run tscx --help

# Or run via Python module
uv run python -m tscx --help
```

### Using Traditional pip/venv

Alternatively, you can use the traditional approach:

```bash
cd tscx
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e '.[test]'
```

To run the tests:
```bash
python -m pytest
```

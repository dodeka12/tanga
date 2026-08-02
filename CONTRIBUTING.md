# Contributing

Contributions are welcome. Please follow the workflow below.

→ **[Full contributing guide](https://dodeka12.github.io/tanga/dev/guides/contributing/)**

## Quick Start

```bash
git clone https://github.com/dodeka12/tanga.git
cd tanga
uv sync --group dev
uv run pre-commit install
```

The last step activates pre-commit hooks that run `ruff` linting/formatting
and block direct commits to `main`.

## Branching Model

1. Create a feature branch from `main`
2. Make your changes and commit
3. Open a pull request to `main`
4. CI runs pytest + C++ tests automatically
5. Merge after PR is approved and CI passes
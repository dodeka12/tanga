# Contributing

This guide covers the workflow for contributing to TanGA.

---

## Setup

```bash
git clone https://github.com/dodeka12/tanga.git
cd tanga
uv sync --group dev
uv run pre-commit install
```

`uv sync --group dev` installs all development dependencies including
pytest, ruff, pre-commit, cmake, ninja, and pybind11.

## Pre-commit Hooks

After running `uv run pre-commit install`, every `git commit` triggers:

| Hook | What it does |
|------|-------------|
| `no-commit-to-branch` | Blocks commits on `main` — always work on a feature branch |
| `ruff` | Lints and auto-fixes Python code (`ruff --fix`) |
| `ruff-format` | Enforces consistent formatting |

If a hook fails, the commit is aborted. Fix the reported issues and
try again.

The hook configuration lives in `.pre-commit-config.yaml` at the repo root.

## Code Style

- **Python:** [PEP 8](https://peps.python.org/pep-0008/) with 100-character
  line length. Ruff enforces these rules automatically via the pre-commit hook
  and the `[tool.ruff]` section in `pyproject.toml`.
- **C++:** See the [C++ coding style guide](cpp-coding-style-guide.md).
- **License headers:** Every new source file must include an
  `SPDX-License-Identifier: Apache-2.0` comment. Run
  `tools/add_license_headers.py` from the repo root to stamp missing headers.

## Branching Model

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes and commit. Pre-commit hooks run automatically.
3. Push your branch and open a pull request to `main`.
4. CI runs the full test suite:
   - Python tests via `pytest`
   - C++ tests via `cmake` build + `ctest`
5. A maintainer reviews and merges the PR. Direct pushes to `main` are
   blocked by branch protection.

## Running Tests

```bash
# Python tests
uv run pytest

# C++ tests
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
cd build && ctest --output-on-failure -j$(nproc)
```

## Documentation

Documentation is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
and deployed automatically to [GitHub Pages](https://dodeka12.github.io/tanga/)
on every merge to `main`.

To preview locally:

```bash
uv run mkdocs serve
```

New features should include documentation updates where appropriate.
See the existing docs under `docs/` for structure and style conventions.

## IDE Configuration

Install a Ruff extension for your editor (VS Code, PyCharm, etc.) to
get inline linting and auto-formatting. The configuration in
`pyproject.toml` is picked up automatically.

## License

TanGA is released under the [Apache License 2.0](https://github.com/dodeka12/tanga/blob/main/LICENSE).
All contributions are made under the same license.
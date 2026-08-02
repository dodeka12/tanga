# Environment & Installation

This guide covers setting up a pytanga development environment and using
pytanga as a dependency in your own project.

## Prerequisites

- **Python ≥ 3.12**
- **uv** (Python package manager and virtual‑environment tool)
- **GCC ≥ 13** (only needed when pytanga must compile its C++ binding from source)

## Development Setup

Clone the repository and sync the `dev` dependency group:

```bash
git clone https://github.com/dodeka12/tanga.git
cd tanga

# Create .venv and install all dev tooling
uv sync --group dev
```

### What `--group dev` installs

The `dev` group (defined in `pyproject.toml` under `[dependency-groups]`)
pulls in:

| Package | Purpose |
|---------|---------|
| `pytest>=9.1.1` | Test runner |
| `ruff>=0.14.0`  | Linter and formatter |
| `tanga-py[compile,examples]` | The pytanga package itself plus its `compile` and `examples` extras |

The extras in turn provide:

| Extra | Packages | Needed for |
|-------|----------|------------|
| `compile` | `pybind11`, `cmake`, `ninja` | Compiling the C++ binding from source |
| `examples` | `scipy`, `ipykernel`, `jupyter`, `ipython` | Running iterative solvers and jupyter notebooks in example scripts under `py/examples/` |

After syncing you can run tests, lint, and execute example scripts:

```bash
uv run pytest
uv run ruff check py/
uv run python py/examples/solver_rotor_estimation.py
```

## Using pytanga as a Dependency

### Pre-Compiled Wheels (recommended for Linux x86_64)

If a pre-compiled wheel exists for your platform, simply:

```bash
pip install tanga-py
```

No C++ compiler or build tools are needed. pytanga ships precompiled
bindings for the five most common algebra configurations:

| Algebra | dim | sig | dtype |
|---------|-----|-----|-------|
| E3 (Euclidean) | 3 | 0 | float64 |
| P3 / PGA3 (Projective) | 4 | 8 | float64 |
| N3 (Conformal) | 5 | 16 | float64 |
| E3 modular (crypto) | 3 | 0 | int64 |
| Sparse high-dim (crypto) | 10 | 0 | int64 |

### Source Compilation (all platforms)

If no pre-compiled wheel is available for your platform, or if you need
an algebra not covered by the precompiled set, add the `compile` extra:

```bash
pip install "tanga-py[compile]"
```

This pulls in cmake, ninja, and pybind11 for on-the-fly compilation.

For the example scripts and iterative solvers, add the `examples` extra as
well:

```bash
pip install "tanga-py[compile,examples]"
```

### With uv

In your own project, add pytanga with uv:

```bash
uv add tanga-py
uv add "tanga-py[compile]"
uv add "tanga-py[compile,examples]"
```

### Virtual environment

The uv commands above automatically create and manage a `.venv/` for your
project.  There is nothing else to set up — uv handles the Python
interpreter, package installation, and environment activation transparently
via `uv run`.

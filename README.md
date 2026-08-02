# TanGA

TanGA is a **geometric algebra library** consisting of two parts:

- **TanGA (C++)** — A header-only C++ template library for geometric algebra
  in high-dimensional vector spaces (up to 32 basis vectors, 2³² blades). It
  provides sparse dynamic multivectors, subspace multivectors, matrix-based
  equation solving, and modular (congruence) arithmetic — making GA practical
  in dimensions where dense representations would be impossible.

- **pytanga (Python)** — A Python package that wraps the C++ engine via
  pybind11. Because each `(dimension, signature)` combination defines a
  distinct algebra, pytanga generates and compiles a dedicated C++ extension
  on the fly the first time an algebra is used, then caches the binary on
  disk. Python code works with a clean, high-level API (`Algebra`, `MV`,
  named `Basis` classes) while the heavy arithmetic runs at full C++ speed.

**→ [Full documentation](docs/index.md)** — C++ and Python API guides,
architecture overview, notebooks, and developer workflows.

## Prerequisites

| Tool | Version | How to get |
|------|---------|-----------|
| GCC (g++) | ≥ 13 | `sudo apt install build-essential` |
| uv | any recent | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Git | any | `sudo apt install git` |

`cmake` and `ninja` are installed automatically by uv as Python packages — no
system installation is needed.

## Set Up the Environment

```bash
# Clone the repo
git clone https://github.com/dodeka12/tanga.git
cd tanga

# Create the virtual environment and install all dev dependencies
uv sync --group dev
```

This installs `pytest`, `ruff`, `cmake`, `ninja`, `pybind11`, and `scipy` into `.venv/`.
The `dev` group includes the `compile` and `examples` extras automatically — see below.

### Extras (when using pytanga as a dependency)

When depending on pytanga in your own project, you can opt into optional extras:

| Extra | Installs | Purpose |
|-------|----------|---------|
| `compile` | `pybind11`, `cmake`, `ninja` | Compile the C++ binding from source — only needed if your algebra is not covered by precompiled wheels or you're on an unsupported platform |
| `examples` | `scipy>=1.13` | Dependencies required to run the example scripts in `py/examples/` |

**With pip — precompiled wheels (recommended):**

```bash
pip install tanga-py
```

Precompiled wheels include bindings for E3, P3, N3, PGA3 (float64) and modular
algebras E3 (int64) and G(10,0) (int64). No C++ compiler or build tools required.

If you need an algebra outside the precompiled set, add the `compile` extra:

```bash
pip install "tanga-py[compile]"
pip install "tanga-py[compile,examples]"
```

**With uv:**

```bash
uv add tanga-py
uv add "tanga-py[compile]"
uv add "tanga-py[compile,examples]"
```

For development of pytanga itself, use `uv sync --group dev` — it brings in both extras plus
`pytest` and `ruff`.

## Build the Example Programs

```bash
# Configure (once, or whenever CMakeLists.txt changes)
uv run cmake -B build -S . \
  -G Ninja \
  -DCMAKE_C_COMPILER=gcc \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_BUILD_TYPE=Release

# Build all targets
uv run cmake --build build --parallel
```

Executables are written to `build/bin/`.

## Run the Example Programs

```bash
./build/bin/Test_Math_01      # matrix and modular arithmetic basics
./build/bin/Test_Basics_01    # multivector algebra operations
./build/bin/Test_Crypt_03     # NTRU-style GA public-key workflow
./build/bin/Test_Crypt_04     # extended workflow with consistency check
```

## Repository Structure

```
cpp/
  Tan.Core/        # bit utilities, assertions, value formatting
  Tan.Math/        # matrix algebra, Gaussian elimination, congruence arithmetic
  Tan.GA/          # blade types, multivector representations, GA products, inversion
  Tan.Crypt/       # cryptographic key-material type stubs (work in progress)
  Tan.App.Test/    # example programs and GA/crypto experiments

py/
  pytanga/         # Python package (pybind11 auto-compile binding)
  examples/        # runnable demo scripts
  tests/           # pytest suite
  cmake/           # CMakeLists.txt for the binding build

docs/
  index.md         # top-level documentation index
  cpp/             # C++ API guides
  py/              # pytanga (Python) guides
  dev/             # architecture notes, type-system docs, workflow guides
  analysis/        # research notes on NTRU in GA and modulus sizing

dev/
  todos/           # implementation plans
```

The module dependency order is strictly:
`Tan.Core` → `Tan.Math` → `Tan.GA` → `Tan.App.Test`

## Documentation

Start with [docs/index.md](docs/index.md) for the full documentation index
covering C++ API guides, pytanga reference, architecture notes, and developer
workflows. The [dev README](docs/dev/README.md) provides a recommended reading
order for contributors.

## License

TanGA is released under the [Apache License 2.0](LICENSE).
Every source file carries an `SPDX-License-Identifier: Apache-2.0` comment.

## AI Tool Documentation Access

When pytanga is installed as a dependency, the markdown documentation is
packaged with the wheel under `pytanga/_docs/`. AI coding tools (Copilot,
Claude Code, etc.) can access this documentation by calling:

```python
import pytanga
pytanga.install_docs()
```

This creates a symlink at `.dep-docs/pytanga/` in the current repository root
pointing to the packaged docs (or the local `docs/` directory in dev mode).
AI tools can then read e.g. `.dep-docs/pytanga/py/geometry/entities.md` without
needing the full source checkout.


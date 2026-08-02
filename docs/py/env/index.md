# Environment & Setup

This page describes how to set up a working pytanga development environment.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **uv** | ≥ 0.5 | Package manager and virtual environment |
| **Python** | ≥ 3.10 | Runtime (managed by uv) |
| **C++ compiler** | GCC ≥ 9, Clang ≥ 14, or MSVC ≥ 2019 | Compilation of generated pybind11 bindings |
| **CMake** | ≥ 3.18 | Build system for binding modules |

## Quick Setup

```bash
# Clone the repository
git clone https://github.com/dodeka12/tanga.git
cd tanga

# Install all dependencies (including dev tools)
uv sync --all-extras
```

## How Compilation Works

pytanga uses **on‑demand JIT compilation**:

1. You import an `Algebra` with specific `(dim, sig, dtype)` parameters.
2. pytanga generates a C++ pybind11 binding file from a template.
3. CMake compiles it into a shared library (`.so`/`.dylib`/`.pyd`).
4. The result is **cached** in `~/.cache/pytanga/` — subsequent imports are instant.

The three non‑template source files compiled into every binding are:

| File | Purpose |
|------|---------|
| `Tan.Math/ValuePrecision.cpp` | `template<>` default precision specialisations |
| `Tan.Core/ValueFormatString.cpp` | Format string specialisations |
| `Tan.Math/Matrix.Enum.cpp` | Non‑template `ToString(EMatrixResult)` |

No pre‑built shared library is required.

## Running Tests

```bash
uv run pytest py/tests/
```

## Running Examples

```bash
uv run python py/examples/algebra_demo.py
```

## Building Documentation

See [MkDocs Publishing](../../dev/workflows/mkdocs-publishing.md) for instructions on building and deploying this documentation site.

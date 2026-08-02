# Phase 0 — Repository Scaffolding

**Overview plan:** [plan.md](plan.md)  
**Depends on:** nothing  
**Required by:** all other phases

---

## Goal

Create the `pytanga/` source tree and project metadata files. All subsequent
phases add content to this skeleton. Do not write any real logic here — just
stub files so that imports resolve and CI can discover the package.

---

## Steps

### 0.1 Create the directory tree ✓

```
pytanga/
  __init__.py              # stub — filled in Phase 6
  _blade_names.py          # stub — filled in Phase 1
  _codegen.py              # stub — filled in Phase 3
  _build.py                # stub — filled in Phase 4
  _cache.py                # stub — filled in Phase 5
  _template.cpp            # filled in Phase 3
  cmake/
    binding/
      CMakeLists.txt       # filled in Phase 2
  tests/
    __init__.py
    test_blade_names.py    # stub — filled in Phase 7
    test_cache.py          # stub — filled in Phase 7
    test_algebra_e3.py     # stub — filled in Phase 7
    test_modular.py        # stub — filled in Phase 7
```

Each stub Python file should contain only a module docstring:
```python
"""pytanga.<module> — see todos/pytanga/phase<N>.md for implementation."""
```

### 0.2 Write `pyproject.toml` ✓

Place at repo root alongside the existing `CMakeLists.txt`.

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "pytanga"
dynamic = ["version"]
description = "Python bindings for the TanGA geometric algebra library"
requires-python = ">=3.10"
dependencies = []          # runtime deps are zero; pybind11 is build-only

[project.optional-dependencies]
build = ["pybind11>=2.11", "cmake>=3.18", "ninja"]
dev   = ["pytanga[build]", "pytest>=7"]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.targets.wheel]
packages = ["pytanga"]
```

### 0.3 Verify the toolchain ✓

Run these commands and confirm they succeed before moving to Phase 2:

```bash
# Add build and dev dependencies via uv
uv add --optional build "pybind11>=2.11" "cmake>=3.18" ninja
uv add --dev pytest

# Sync the environment with all extras
uv sync --all-extras

# Verify pybind11 cmake integration
uv run python -c "import pybind11; print(pybind11.get_cmake_dir())"

# Verify cmake version (must be >= 3.18) and gcc toolchain
cmake --version
gcc --version
g++ --version
```

Record the pybind11 cmake directory — the binding CMakeLists.txt will use it
as a hint for `find_package(pybind11)`. The C++ binding is always compiled
with **GCC** (`CC=gcc CXX=g++`); this is enforced in the CMake invocation in
Phase 4.

### 0.4 Confirm the tanga source path ✓

All later phases reference `TANGA_SOURCE` as the absolute path to
`<repo>/source`. Decide now how this path is discovered at runtime:

- **Recommended default:** derive it relative to the `pytanga/` package
  directory: `Path(__file__).parent.parent / "source"`. This works when the
  repo is the working directory.
- **Override:** respect a `PYTANGA_TANGA_SOURCE` environment variable.

Document this resolution logic as a constant in the stub `_build.py`:

```python
import os
from pathlib import Path

_REPO_ROOT   = Path(__file__).parent.parent
TANGA_SOURCE = Path(os.environ.get("PYTANGA_TANGA_SOURCE",
                                    _REPO_ROOT / "source")).resolve()
```

### 0.5 Build and run `Tan.App.Test` ✓

The root `CMakeLists.txt` already wires up all four sub-projects
(`Tan.Core`, `Tan.Math`, `Tan.GA`, `Tan.App.Test`). The steps below configure
and build with GCC and run each test executable.

**Prerequisites (system packages)**

```bash
sudo apt install gcc g++ cmake ninja-build   # Debian/Ubuntu
# or: sudo dnf install gcc gcc-c++ cmake ninja-build  # Fedora
```

Confirm versions:

```bash
gcc --version    # >= 11 recommended for C++17 + SSE4.1
cmake --version  # >= 3.18
```

**Configure**

```bash
# From the repo root
cmake -B build -S . \
      -G Ninja \
      -DCMAKE_C_COMPILER=gcc \
      -DCMAKE_CXX_COMPILER=g++ \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_POLICY_VERSION_MINIMUM=3.5
```

The `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` flag is required when using cmake ≥ 4.x
(installed via uv) because the root `CMakeLists.txt` declares an old minimum
version. Drop it if using a system cmake ≤ 3.x.

**Build**

```bash
cmake --build build --parallel
```

Binaries land in `build/bin/`.

**Run the test executables**

```bash
./build/bin/Test_Math_01
./build/bin/Test_Basics_01
./build/bin/Test_Crypt_03
./build/bin/Test_Crypt_04
```

All four executables must exit with code 0.

**Run all at once (convenience)**

```bash
for exe in Test_Math_01 Test_Basics_01 Test_Crypt_03 Test_Crypt_04; do
    echo "=== $exe ===" && ./build/bin/$exe || { echo "FAILED: $exe"; exit 1; }
done
```

---

## Completion check

- [ ] `pytanga/` tree exists with all stub files
- [ ] `pyproject.toml` is at repo root
- [ ] `uv sync --all-extras` succeeds without errors
- [ ] `python -c "import pytanga"` succeeds (imports the stub `__init__.py`)
- [ ] `cmake --version` and `pybind11` cmake dir both print without error
- [ ] `cmake -B build -S . -G Ninja -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release` exits without error
- [ ] `cmake --build build --parallel` compiles all four test executables
- [ ] All four executables (`Test_Math_01`, `Test_Basics_01`, `Test_Crypt_03`, `Test_Crypt_04`) exit with code 0

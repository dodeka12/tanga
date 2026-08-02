# Phase 4 — Build Driver

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 0 (paths), Phase 2 (cmake file), Phase 3 (codegen)  
**Required by:** Phase 5 (cache calls the build driver on a miss)

---

## Goal

Implement `pytanga/_build.py` — the Python code that invokes cmake to compile
a generated binding `.cpp` into a Python extension module.

---

## Steps

### 4.1 Add imports and constants to `_build.py`

```python
"""Compile a generated binding .cpp into a Python extension module."""

from __future__ import annotations
import os
import platform
import subprocess
import sys
from pathlib import Path

import pybind11

_REPO_ROOT    = Path(__file__).parent.parent
TANGA_SOURCE  = Path(os.environ.get(
    "PYTANGA_TANGA_SOURCE", _REPO_ROOT / "source")).resolve()

_BINDING_CMAKE = Path(__file__).parent / "cmake" / "binding" / "CMakeLists.txt"
_PYBIND11_DIR  = pybind11.get_cmake_dir()
```

### 4.2 Implement `build_binding()`

```python
def build_binding(
    binding_cpp: Path,
    build_dir: Path,
    module_name: str,
    *,
    tanga_source: Path = TANGA_SOURCE,
    verbose: bool = False,
) -> Path:
    """
    Configure and build a pybind11 binding.

    Parameters
    ----------
    binding_cpp:   absolute path to the generated .cpp file
    build_dir:     cmake build directory (will be created)
    module_name:   Python module name (no extension)
    tanga_source:  path to <repo>/source
    verbose:       pass --verbose to cmake build step

    Returns
    -------
    Path to the compiled extension (.pyd on Windows, .so on Linux/macOS)
    """
    build_dir.mkdir(parents=True, exist_ok=True)

    # --- cmake configure ---
    configure_cmd = [
        "cmake",
        "-S", str(_BINDING_CMAKE.parent),
        "-B", str(build_dir),
        f"-DBINDING_CPP={binding_cpp}",
        f"-DTANGA_SOURCE={tanga_source}",
        f"-DMODULE_NAME={module_name}",
        f"-Dpybind11_DIR={_PYBIND11_DIR}",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_C_COMPILER=gcc",
        "-DCMAKE_CXX_COMPILER=g++",
    ]
    # Use Ninja when available for faster incremental builds
    if _ninja_available():
        configure_cmd += ["-G", "Ninja"]

    _run(configure_cmd, verbose=verbose)

    # --- cmake build ---
    build_cmd = ["cmake", "--build", str(build_dir), "--config", "Release"]
    if verbose:
        build_cmd.append("--verbose")
    _run(build_cmd, verbose=verbose)

    return _find_extension(build_dir, module_name)
```

### 4.3 Implement helper functions

```python
def _run(cmd: list[str], verbose: bool) -> None:
    """Run a subprocess, capturing output unless verbose."""
    result = subprocess.run(
        cmd,
        stdout=None if verbose else subprocess.PIPE,
        stderr=None if verbose else subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        output = result.stdout or ""
        raise RuntimeError(
            f"Command failed (exit {result.returncode}):\n"
            f"  {' '.join(cmd)}\n\n{output}"
        )


def _ninja_available() -> bool:
    return subprocess.run(
        ["ninja", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _find_extension(build_dir: Path, module_name: str) -> Path:
    """
    Locate the compiled extension in *build_dir*.

    CMake places the output at build_dir root (see LIBRARY_OUTPUT_DIRECTORY
    in phase 2's CMakeLists.txt).  The extension suffix is platform-specific.
    """
    suffixes = (
        [".pyd"] if platform.system() == "Windows"
        else [".so"]
    )
    # Also accept CPython ABI suffixes like .cpython-312-x86_64-linux-gnu.so
    for path in sorted(build_dir.rglob(f"{module_name}*")):
        if path.suffix in suffixes or ".so" in path.name:
            return path
    raise FileNotFoundError(
        f"Extension for {module_name!r} not found in {build_dir}"
    )
```

### 4.4 Add a `build_and_load()` convenience function

Used by the facade (Phase 6) to do the full codegen → compile → import sequence
without caring about intermediate file paths.

```python
def build_and_load(
    dim: int,
    sig: int,
    dtype: str,
    build_dir: Path,
    *,
    tanga_source: Path = TANGA_SOURCE,
    verbose: bool = False,
):
    """
    Generate, compile, and import a binding for (dim, sig, dtype).

    Returns
    -------
    tuple[module, Path]
        The imported module object and the absolute path to the compiled
        extension (.so / .pyd). The caller (Phase 5 cache) needs the path
        to write meta.json without re-discovering it via _find_extension.
    """
    import importlib.util
    from pytanga._codegen import generate, module_name as mk_module_name

    mod_name = mk_module_name(dim, sig, dtype)
    cpp_path = build_dir / f"{mod_name}.cpp"

    generate(dim, sig, dtype, cpp_path)

    so_path = build_binding(
        binding_cpp=cpp_path,
        build_dir=build_dir / "cmake_build",
        module_name=mod_name,
        tanga_source=tanga_source,
        verbose=verbose,
    )

    spec = importlib.util.spec_from_file_location(mod_name, so_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, so_path
```

### 4.5 End-to-end smoke test

Run this manually before moving to Phase 5:

```python
from pathlib import Path
from pytanga._build import build_and_load

mod, so_path = build_and_load(3, 0, "float64", Path("/tmp/pytanga_test"), verbose=True)
print(so_path)             # absolute path to the compiled .so
print(mod.ALGEBRA_DIM)     # expected: 8
a = mod.DynMV()
a.set(1, 1.0)              # e1 = 1.0
b = mod.DynMV()
b.set(1, 1.0)              # e1 = 1.0
c = mod.gp(a, b)           # e1 * e1 in G(3,0) = scalar 1
print(c.to_dict())         # expected: {0: 1.0}
```

If compilation fails, run with `verbose=True` to see the full cmake output.
Common issues:
- pybind11 not found → confirm `pybind11.get_cmake_dir()` returns a valid path
- Missing tanga headers → confirm `TANGA_SOURCE` points to `<repo>/source`
- MSVC not on PATH → open a VS Developer Command Prompt or run
  `cmake -G "Visual Studio 17 2022"` instead of Ninja

---

## Completion check

- [ ] `pytanga/_build.py` is fully implemented
- [ ] `build_and_load(3, 0, "float64", ...)` succeeds and returns a module
- [ ] `mod.gp(a, b)` where `a = b = e1` returns `{0: 1.0}` (scalar 1)
- [ ] `build_and_load(3, 0, "int64", ...)` also compiles (int64 path)
- [ ] A second call with the same `build_dir` does not recompile (cmake is
  already configured; the build step is a no-op when nothing changed)

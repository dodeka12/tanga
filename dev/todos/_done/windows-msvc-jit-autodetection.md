# Windows MSVC Auto-Detection for the JIT Compile Path

**Created:** 2026-08-19 | **Status:** Done

## Overview

The JIT compile path (`py/pytanga/codegen/_build.py`) compiles C++ algebra bindings on
demand via CMake. On Windows it hardcodes the compiler name `cl.exe`, which only resolves
when the caller has already sourced the MSVC developer environment (the
"Developer Command Prompt for VS"). This plan makes `_build.py` locate MSVC itself (via
`vswhere`) and source the toolchain environment (`vcvars64.bat`) automatically, so users
no longer need the developer shell to JIT-compile an algebra binding.

> Implemented 2026-08-19 (commit 0a983ef).

## Current State (verified 2026-08-19 on this machine)

| Item | Status |
|------|--------|
| MSVC | ✅ installed — VS 18 Build Tools, MSVC 14.51.36231 |
| `vswhere.exe` | ✅ `C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe` |
| `vcvars64.bat` | ✅ `<VS>\VC\Auxiliary\Build\vcvars64.bat` |
| `ninja` / `cmake` / `pybind11` | ✅ in `.venv\Scripts` (from the `[compile]` extra) |
| `cl.exe` on `PATH` | ❌ only after `vcvars64.bat` has run |

### The failing call (from `_build.py`)

```text
cmake -S …/codegen -B …/cmake_build … -DCMAKE_CXX_COMPILER=cl.exe -G Ninja
CMake Error: The CMAKE_CXX_COMPILER: cl.exe is not a full path and was not found in the PATH.
```

`cl.exe` is passed as a bare name, so CMake needs MSVC on `PATH`.

### Verified working mechanism

1. `vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`
   → `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools`
2. `cmd /c "call "<VS>\VC\Auxiliary\Build\vcvars64.bat" >nul && set"` captures the full
   MSVC environment (~99 vars: `PATH` with `cl.exe` at `…\bin\HostX64\x64`, plus
   `INCLUDE`, `LIB`, `LIBPATH`).
3. Merging those vars into the CMake subprocess environment lets
   `-DCMAKE_CXX_COMPILER=cl.exe` resolve.

## Implementation

All changes are in `py/pytanga/codegen/_build.py`.

### 1. Imports

Add `import functools` and `import shutil` to the existing imports
(alongside `os`, `platform`, `subprocess`, `sys`, `pathlib.Path`).

### 2. Add `_locate_vcvars64() -> str | None`

Guard on `platform.system() == "Windows"`.

1. Locate `vswhere.exe`:
   - `os.environ["ProgramFiles(x86)"] + r"\Microsoft Visual Studio\Installer\vswhere.exe"`,
     checked with `Path(...).is_file()`;
   - fallback `shutil.which("vswhere")`.
   - If neither resolves, return `None`.
2. Run
   `vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`
   via `subprocess.run(..., capture_output=True, text=True)` (catch
   `OSError`/`subprocess.SubprocessError`; return `None` on non-zero exit).
3. Return `<installPath>\VC\Auxiliary\Build\vcvars64.bat` if it exists, else `None`.

### 3. Add `_msvc_environment() -> dict[str, str]`

- Cache with `@functools.lru_cache(maxsize=1)` (the env capture is ~1 s and only needs
  to run once per process).
- `vcvars = _locate_vcvars64()`; if `None`, return `{}`.
- Run `cmd /c 'call "<vcvars>" >nul && set'` via
  `subprocess.run(..., shell=True, capture_output=True, text=True, errors="replace")`.
- Parse each `KEY=VALUE` line into a dict and return it. (Empty on failure.)

### 4. Thread the environment through `_run`

Change `_run(cmd: list[str], verbose: bool)` →
`_run(cmd: list[str], verbose: bool, env: dict[str, str] | None = None)` and forward
`env=env` to the `subprocess.run` calls inside. Default `None` = inherit (preserves
current behavior on all platforms).

### 5. Inject the env in `build_binding`

After the compiler is resolved (currently line 77) and before `_run(configure_cmd, …)`:

```python
run_env = None
if _SYSTEM == "Windows" and os.environ.get("PYTANGA_CXX_COMPILER") is None \
        and shutil.which("cl.exe") is None:
    msvc_env = _msvc_environment()
    if msvc_env:
        run_env = {**os.environ, **msvc_env}
```

Then pass `env=run_env` to both `_run(configure_cmd, …)` and `_run(build_cmd, …)`.

- **Fast path:** when `cl.exe` is already on `PATH` (i.e. a developer shell), `run_env`
  stays `None` and nothing changes.
- **Override preserved:** `PYTANGA_CXX_COMPILER` (env var) still wins — when set, we
  skip auto-detection entirely and pass the explicit compiler name as today.
- **Non-Windows / MSVC-absent:** `run_env` stays `None`; behavior is unchanged (CMake
  reports its usual "no compiler" error).

### 6. Fix `_ninja_available()`

`subprocess.run(["ninja", "--version"], …)` currently raises `FileNotFoundError` when
ninja is absent (uncaught). Wrap it in `try/except (FileNotFoundError, OSError)` and
return `False` on failure.

## Verification

From a **plain** PowerShell (no developer shell):

1. Clear any cached binding, then
   `uv run python -c "from pytanga.basis import BasisP3; BasisP3()"` succeeds and shows
   the compile step (no `cl.exe … not found` error).
2. `uv run python -c "from pytanga.basis import BasisE3; BasisE3()"` (second algebra,
   cached) loads instantly.
3. `PYTANGA_CXX_COMPILER=__bogus__ uv run python -c "… BasisE3() …"` fails again with a
   CMake compiler error, confirming the explicit override still takes precedence.
4. From a developer shell (where `cl.exe` is already on `PATH`), the fast path is hit and
   behavior is unchanged.

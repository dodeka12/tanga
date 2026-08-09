# MSVC / Windows Compilation Support

**Created:** 2026-08-03 | **Status:** Planned

## Overview

Extend the algebra JIT compilation pipeline (`py/pytanga/codegen/_build.py`) and
the associated tools / CI so that on-the-fly binding compilation works under
Windows with the Microsoft Visual C++ (MSVC) toolchain.  This must also work
when pre-compiling algebras for packaging in a platform wheel and inside a
GitHub Actions workflow.

---

## Implementation Checklist

- [x] Step 1: `_build.py` — compiler detection and CMake configure
- [x] Step 2: `_build.py` — tighten `_find_extension()` per-platform suffix matching
- [x] Step 3: `codegen/CMakeLists.txt` — add `/bigobj` for MSVC
- [x] Step 4: `_cache.py` — `_load_precompiled()` uses platform-aware extension
- [x] Step 5: `tools/build-precompiled.py` — MSVC detection + `.pyd` handling
- [x] Step 6: `.github/workflows/ci.yml` — add `windows-latest` test job
- [x] Step 7: `.github/workflows/publish.yml` — add `build-windows` wheel job
- [x] Step 8: Update existing docs — per-file changes detailed below
- [x] Step 9: Add compiler installation guide — new `## Compiler Setup` section in `installation.md`

---

## Problem

The current build driver hard-codes `g++` as the compiler and assumes Linux
conventions throughout:

1. **`_build.py` line 75** — passes `-DCMAKE_CXX_COMPILER=g++` unconditionally.
   On Windows without g++ in `PATH` this fails immediately.

2. **`_build.py` `_find_extension()`** — uses a fragile `".so" in path.name`
   substring test that can match false positives.

3. **`codegen/CMakeLists.txt`** — already has `if(MSVC)` for optimisation flags
   but is missing `/bigobj`, which is essential for pybind11's large translation
   units with MSVC (prevents "too many sections" `C1128`).

4. **`_cache.py` `_load_precompiled()`** — searches only for `.so` files when
   loading precompiled bundles; needs `.pyd` on Windows.

5. **`tools/build-precompiled.py`** — `_detect_compiler()` only probes `g++`;
   the `.so` copy logic ignores `.pyd` on Windows.

6. **GitHub Actions** — CI runs only on `ubuntu-24.04`; publish has only
   `build-pure` and `build-linux` jobs (macOS is commented out, no Windows).

7. **Documentation** — says "The compiler is g++" and "GCC ≥ 13" with no
   mention of MSVC.  No installation instructions for Windows or macOS compilers.
   The precompiled-wheels doc and the setup-pypi-publishing todo both imply
   Windows is unsupported ("No Windows — assumes a Unix toolchain").

---

## Design Decisions

- **Compiler selection**: detect platform default (`cl.exe` / `g++` / `clang++`)
  but allow override via `PYTANGA_CXX_COMPILER` env var.
- **CMake generator**: allow explicit override via `PYTANGA_CMAKE_GENERATOR`
  env var (e.g. `"Visual Studio 17 2022"`, `"Ninja"`).  When unset:
  - Windows + MSVC → default to `"Ninja"` (ninja is in the `compile` extra).
  - All other cases → let CMake auto-detect.
- **Extension suffix**: `.pyd` on Windows, `.so` on Linux, `.so`/`.dylib` on macOS.
- **CI**: Windows jobs use the pre-installed Visual Studio 2022 toolchain on
  `windows-latest` GitHub runners.

---

## Detailed Steps

### Step 1 — `_build.py`: Compiler Detection & CMake Configure

**File:** `py/pytanga/codegen/_build.py`

**Changes:**

1. Add a module-level helper `_detect_default_compiler()` that returns the
   platform default:
   - `Windows` → `"cl.exe"`
   - `Darwin` → `"clang++"`
   - `Linux` / other → `"g++"`

2. Add a helper `_resolve_generator()` that:
   - Returns `PYTANGA_CMAKE_GENERATOR` if set.
   - On Windows with MSVC compiler → `"Ninja"` if ninja is available.
   - Otherwise → `None` (let CMake auto-detect).

3. In `build_binding()`, replace the hard-coded `"-DCMAKE_CXX_COMPILER=g++"`
   with:
   ```python
   compiler = os.environ.get("PYTANGA_CXX_COMPILER", _detect_default_compiler())
   configure_cmd.extend([f"-DCMAKE_CXX_COMPILER={compiler}"])
   ```

4. Replace the inline ninja check with `_resolve_generator()`:
   ```python
   gen = _resolve_generator()
   if gen:
       configure_cmd += ["-G", gen]
   ```

### Step 2 — `_build.py`: Tighten `_find_extension()`

**File:** `py/pytanga/codegen/_build.py`

**Current (fragile):**
```python
suffixes = [".pyd"] if platform.system() == "Windows" else [".so"]
for path in sorted(build_dir.rglob(f"{module_name}*")):
    if path.suffix in suffixes or ".so" in path.name:
        return path
```

**Replace with:**
```python
_ext_map = {"Windows": [".pyd"], "Darwin": [".so", ".dylib"], "Linux": [".so"]}
suffixes = _ext_map.get(platform.system(), [".so"])
for path in sorted(build_dir.rglob(f"{module_name}*")):
    if path.suffix in suffixes:
        return path
```

### Step 3 — `codegen/CMakeLists.txt`: MSVC `/bigobj`

**File:** `py/pytanga/codegen/CMakeLists.txt`

Inside the existing `if(MSVC)` block (line 59), add the `/bigobj` flag:
```cmake
if(MSVC)
    target_compile_options(${MODULE_NAME} PRIVATE /bigobj /arch:SSE4.1 /O2)
else()
    target_compile_options(${MODULE_NAME} PRIVATE -msse4.1 -mpopcnt -O3)
endif()
```

### Step 4 — `_cache.py`: Platform-Aware Precompiled Loading

**File:** `py/pytanga/codegen/_cache.py`

In `_load_precompiled()`, change the file glob from looking only for `.so` to
using a platform-aware extension list, mirroring the logic from Step 2.

Also ensure the `precompiled/` directory lookup uses a helper like:
```python
def _precompiled_ext() -> str:
    return ".pyd" if platform.system() == "Windows" else ".so"
```

### Step 5 — `tools/build-precompiled.py`: MSVC Detection + `.pyd`

**File:** `tools/build-precompiled.py`

**Changes:**

1. `_detect_compiler()`: probe `cl.exe` on Windows before `g++`:
   ```python
   def _detect_compiler() -> str:
       import subprocess
       if platform.system() == "Windows":
           try:
               out = subprocess.run(["cl"], capture_output=True, text=True, timeout=5)
               # cl prints banner to stdout even without args
               return out.stdout.splitlines()[0] if out.returncode == 0 else "unknown"
           except Exception:
               pass
       try:
           out = subprocess.run(["g++", "--version"], capture_output=True, text=True, timeout=5)
           return out.stdout.splitlines()[0] if out.returncode == 0 else "unknown"
       except Exception:
           return "unknown"
   ```

2. When copying `.so` from cache, use `.pyd` extension on Windows for the
   destination filename.

3. Record `"ext": ".pyd"` or `"ext": ".so"` in the manifest for each algebra.

### Step 6 — `ci.yml`: Windows Test Job

**File:** `.github/workflows/ci.yml`

Add a parallel `test-windows` job:

```yaml
  test-windows:
    name: Test (Windows, pytest)
    runs-on: windows-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install Python toolchain
        run: uv sync --group dev

      - name: Run pytest
        run: uv run pytest
```

Note: The C++ test build (`cmake --build` + `ctest`) is Linux-only — we skip
it on Windows since the main `CMakeLists.txt` at the repo root is not needed
for the binding compilation and adds complexity with test executables.

### Step 7 — `publish.yml`: Windows Wheel Build

**File:** `.github/workflows/publish.yml`

Add a `build-windows` job modeled on `build-linux`:

```yaml
  build-windows:
    name: Build Windows wheel (win_amd64)
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Sync dependencies
        run: uv sync --group dev

      - name: Build precompiled
        run: uv run python tools/build-precompiled.py

      - name: Build wheel
        if: inputs.version == ''
        run: uv build --wheel

      - name: Build wheel (forced version)
        if: inputs.version != ''
        run: |
          $env:SETUPTOOLS_SCM_PRETEND_VERSION = "${{ inputs.version }}".TrimStart('v')
          uv build --wheel

      - uses: actions/upload-artifact@v4
        with:
          name: wheels-windows
          path: dist/*.whl
```

Update the `publish` job's `needs` to include `build-windows`:
```yaml
    needs: [build-pure, build-linux, build-windows]
```

### Step 8 — Update Existing Documentation

Five files need updates to reflect multi-platform support.

#### 8a. `docs/py/env/installation.md`

**Line 10** — `## Prerequisites`:

Change:
> - **GCC ≥ 13** (only needed when pytanga must compile its C++ binding from source)

To:
> - **C++ compiler** — only needed when pytanga must compile its C++ binding
>   from source (i.e. when no pre-compiled wheel exists for your platform or
>   you use a custom algebra).  See [Compiler Setup](#compiler-setup) below
>   for per-platform installation instructions.

**Line 52** — `### Pre-Compiled Wheels` heading:

Change:
> ### Pre-Compiled Wheels (recommended for Linux x86_64)

To:
> ### Pre-Compiled Wheels (recommended)

(Now that we ship Windows wheels too.)

**Line 71** — `### Source Compilation (all platforms)`:

Add a sentence directing readers to the Compiler Setup section:
> This pulls in cmake, ninja, and pybind11 for on-the-fly compilation.
> You also need a C++ compiler — see [Compiler Setup](#compiler-setup).

#### 8b. `docs/py/env/compile-and-binding.md`

**Line 65**:

Change:
> The compiler is `g++` and the build type is `Release`.

To:
> The compiler is `g++` (Linux), `clang++` (macOS), or `cl.exe` (Windows/MSVC),
> and the build type is `Release`.  See the [installation guide](installation.md#compiler-setup)
> for per-platform compiler setup.

#### 8c. `docs/dev/workflows/precompiled-wheels.md`

This file uses "`.so`" throughout as a generic term for compiled extensions and
references platform-specific scripts.  Update to acknowledge `.pyd` on Windows:

**Line 4**: "precompiled `.so` files" → "precompiled extension modules (`.so` / `.pyd`)"

**Line 12**: "harvest `.so` files" → "harvest compiled extension files"

**Line 43**: "with precompiled `.so` files" → "with precompiled extension modules"

**Line 53**: Add a note:
> On Windows, the compiled extensions use the `.pyd` suffix. The tools
> handle this platform difference automatically.

**Line 66**: "compiled `.so`" → "compiled extension"

**Line 68**: "copies each `.so`" → "copies each compiled extension"

**Line 118**: "precompiled `.so` files" → "precompiled extension modules"

**Line 132**: "`.so` already exists" → "compiled extension already exists"

**Line 135**: "copy the `.so`" → "copy the extension"

**Line 149-166** (Directory Layout): Add a note that on Windows the files would
be `.pyd` instead of `.so`.

#### 8d. `dev/todos/setup-pypi-publishing.md`

**Lines 66-67**:

Change:
> **No Windows** — the JIT compilation pipeline (`build-precompiled.py`) assumes a Unix
> toolchain (g++/clang++ via CMake).

To:
> **Windows** — supported via `windows-latest` runner.  The JIT compilation
> pipeline uses MSVC (`cl.exe`) on Windows.  Precompiled `.pyd` files are
> bundled into `win_amd64` wheels.

Also add a row to the Wheel Build Matrix table (line 59-64):
> | `build-platform` | `windows-latest` | `cp312-cp312-win_amd64` |

#### 8e. `docs/py/viz/visualizer.md`

**Line 273**:

Change:
> Under WSL or headless environments where automatic browser open is unsupported,

To:
> Under WSL, native Windows, or headless environments where automatic browser
> open is unsupported,

(This makes it clear Windows users can run natively, not only via WSL.)

### Step 9 — New Doc Section: Per-Platform Compiler Installation

**File:** `docs/py/env/installation.md`

Add a new `## Compiler Setup` section after the Prerequisites section that gives
concrete, copy-paste installation commands for each platform:

```markdown
## Compiler Setup

pytanga compiles its C++ binding on-demand using CMake and a C++17 compiler.
The `[compile]` extra (`pip install "tanga-py[compile]"`) pulls in `cmake`,
`ninja`, and `pybind11` via pip — but **you must provide the C++ compiler**
separately.

Choose your platform below.

### Linux

Install GCC (recommended) or Clang via your package manager:

```bash
# Ubuntu / Debian
sudo apt install build-essential g++-13

# Fedora
sudo dnf install gcc-c++

# Arch
sudo pacman -S gcc
```

Verify:

```bash
g++ --version   # should show ≥ 13.x
```

Alternatively, install Clang:

```bash
# Ubuntu / Debian
sudo apt install clang-14

# Fedora
sudo dnf install clang
```

### macOS

Install the Xcode Command Line Tools (provides `clang++`):

```bash
xcode-select --install
```

Or install GCC via Homebrew:

```bash
brew install gcc
```

Verify:

```bash
clang++ --version   # should show ≥ 14.x
```

### Windows

You need the **Microsoft Visual C++ (MSVC)** toolchain.  There are three
options:

#### Option A: Visual Studio Build Tools (recommended)

1. Download the **Build Tools for Visual Studio 2022** from
   [visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
2. Run the installer and select the **"Desktop development with C++"** workload.
3. After installation, open the **"Developer Command Prompt for VS 2022"**
   from the Start Menu and run all `pip` / `uv` commands from that terminal.

#### Option B: Full Visual Studio 2022 Community Edition

1. Download **Visual Studio 2022 Community** (free) from
   [visualstudio.microsoft.com/vs/community/](https://visualstudio.microsoft.com/vs/community/)
2. During installation, select the **"Desktop development with C++"** workload.
3. Use the **"Developer Command Prompt for VS 2022"** or launch VS Code from
   the Developer Command Prompt (`code .`).

#### Option C: VS Code with C++ Extension

1. Install the **C/C++** extension (`ms-vscode.cpptools`) in VS Code.
2. Install the Build Tools from Option A.
3. Open your project folder; VS Code should detect MSVC automatically.

Verify (from the Developer Command Prompt):

```cmd
cl   :: should print the Microsoft C/C++ compiler version
```

> **Important:** CMake on Windows must be run from a terminal that has MSVC in
> its `PATH`.  The "Developer Command Prompt" configures this automatically.
> Without it, `cmake` will report `No CMAKE_CXX_COMPILER could be found`.

### Alternative: WSL (Windows Subsystem for Linux)

If you prefer a Linux toolchain on Windows, install WSL and a Linux distribution
(Ubuntu recommended), then follow the Linux instructions above inside the WSL
terminal.

```powershell
# From an Administrator PowerShell:
wsl --install -d Ubuntu
```

After installation, open the Ubuntu terminal and follow the [Linux](#linux)
instructions.
```

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `cl.exe` not in PATH on user machines (MSVC requires Developer Command Prompt) | Medium | GitHub runners have MSVC pre-configured. For end users, documented in Compiler Setup section with three installation options + the Developer Command Prompt requirement prominently called out. |
| Ninja not installed on Windows | Low | `ninja` is in the `compile` extra (`pyproject.toml` line 24) and is available on PyPI for Windows. |
| `/bigobj` flag breaks older MSVC versions | Very low | `/bigobj` is supported since VS 2005; we document MSVC ≥ 2019 as the minimum. |
| Precompiled `.pyd` not compatible across Python versions | Medium | Manifest already records `python_abi`; cache invalidation handles it. The `build-precompiled.py` step runs on the same Python version as the wheel target. |
| Windows wheel tag (`win_amd64`) not set automatically | Low | `hatchling` + `hatch-vcs` auto-detect the platform tag when the wheel contains compiled extensions. `fix-wheel-tag.py` already has a `Windows` → `win_amd64` branch. Verify after Step 7. |
| macOS precompiled still commented out | — | Out of scope for this plan; addressed in a future macOS-specific plan. |

---

## Implementation Order

| Step | File(s) | Effort | Depends on |
|------|---------|--------|------------|
| 1  | `_build.py` | 20 min | — |
| 2  | `_build.py` | 5 min | — |
| 3  | `codegen/CMakeLists.txt` | 2 min | — |
| 4  | `_cache.py` | 10 min | — |
| 5  | `tools/build-precompiled.py` | 15 min | 1, 2 |
| 6  | `ci.yml` | 10 min | 1–4 |
| 7  | `publish.yml` | 15 min | 5 |
| 8  | 5 doc files (see 8a–8e) | 25 min | — |
| 9  | `installation.md` (new section) | 20 min | — |

**Total: ~120 minutes.**

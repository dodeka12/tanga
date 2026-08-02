# Wheel Packaging — Make pytanga Usable as a pip Dependency

**Created:** 2026-07-27 | **Status:** In Progress

## Implementation Checklist

- [x] Step 1: Add C++ sources to wheel via force-include (`pyproject.toml`)
- [x] Step 2: Rename `[build]` → `[compile]` optional-dependencies (`pyproject.toml`)
- [x] Step 3: Move CMakeLists.txt into the package (`py/pytanga/codegen/CMakeLists.txt`)
- [x] Step 4: Update `_build.py` to use `__file__`-relative paths
- [x] Step 5: Remove dead `_template.cpp` references — **REJECTED**: `_generator.py` still actively reads `_template.cpp` at runtime via `_TEMPLATE_PATH`. The template is not dead code.
- [x] Step 6a: Update `README.md` — rename build→compile, add pip+uv dependency install, keep uv dev install
- [x] Step 6b: Update `docs/py/index.md` — (was already fine/no changes needed beyond existing env docs)
- [x] Step 6c: Update `docs/py/env/installation.md` — rename build→compile, add pip instructions section alongside uv
- [x] Step 6d: Update `docs/py/env/compile-and-binding.md` — remove stale `_template.cpp`/`py/cmake/binding/` references
- [x] Step 6e: Move repo layout tree from `docs/py/index.md` to `docs/dev/README.md`
- [x] Step 7: Verify — build wheel, inspect contents (wheel built, all _ga_src/ files present)

## Problem

When a user installs pytanga via `pip install pytanga` (from a wheel), the C++ source
files are missing because:

- **Wheel** only packages `py/pytanga/` (pyproject.toml line 62)
- **sdist** includes `/cpp` (pyproject.toml line 72), so `pip install git+https://…` works

`_build.py` computes paths relative to the repo root (`Path(__file__).parent.parent.parent.parent`),
which resolves to nonsense inside `site-packages/`. On-the-fly compilation fails with:

```
FileNotFoundError: Tan.GA source directory not found: …
```

## Constraint

The `cpp/` directory must **stay at the repo root** — it is an independently usable C++ library.
We must not physically move it into `py/pytanga/`.

## Solution

Use hatchling's `[tool.hatch.build.targets.wheel.force-include]` to **copy** the C++ sources
into the wheel at packaging time under `pytanga/_ga_src/`. The repo layout stays untouched;
the copy only exists inside the built artifact.

At runtime, `_build.py` resolves paths relative to its own `__file__` instead of walking up
to a non-existent repo root.

---

## Files to Bundle

Transitive `#include` closure from `Tan.GA/*.h` (determined by grepping for `#include "Tan.(Core|Math)/"`):

### Tan.GA (27 headers)
```
Algo.h              BasisE3.h           BasisN3.h          BasisP3.h
Blade.h             Blade_Operators.h   BladeMask.h        DynamicMultivector.h
Enum.h              Matrix_BladeMask.h  Matrix_MapToBladeMask.h
Matrix_MapToSubspace.h  Matrix_Product.h   Multivector.h
MultivectorE3.h     MultivectorN3.h     MultivectorP3.h    MultivectorStyle.h
MV_Blade_Ops.h      MV_Operators.h      String.h           SubspaceBasis.h
SubspaceMask.h      SubspaceMultivector.h  SubspaceMultivectorE3.h
SubspaceMultivectorN3.h  SubspaceMultivectorP3.h  Tensor_Product.h
```

Excluded: `_CompileTest_*.cpp`, `CMakeLists.txt`

### Tan.Math (13 headers + 2 .cpp)
```
Congruence.h        FixedGeoTypes.h     FixedVectorMath.h  FixedVectorTypes.h
InlineMath.h        Matrix.h            Matrix.Algo.GE.h   Matrix.Algo.SVD.h
Matrix.Enum.h       Matrix.Operators.h  Tensor.h           ValuePrecision.h
ValuePrecision.cpp  Matrix.Enum.cpp
```

Excluded: `Matrix.cpp`, `CMakeLists.txt`

### Tan.Core (5 headers + 1 .cpp)
```
Array.h             Defines.h           IntrinsicFunctions.h
StdAlgo.h           StrideIterator.h    ValueFormatString.h
ValueFormatString.cpp
```

Excluded: `Array.cpp`, `CMakeLists.txt`

**Total:** ~45 headers + 3 `.cpp` ≈ 350 KB. Negligible wheel size impact.

---

## Implementation Steps

### Step 1: Add C++ sources to wheel via force-include

**File:** `pyproject.toml`

Add to the existing `[tool.hatch.build.targets.wheel.force-include]` section:

```toml
[tool.hatch.build.targets.wheel.force-include]
"py/pytanga/_template.cpp" = "pytanga/_template.cpp"

# Vendored C++ sources for on-the-fly compilation
"cpp/Tan.GA" = "pytanga/_ga_src/Tan.GA"
"cpp/Tan.Math" = "pytanga/_ga_src/Tan.Math"
"cpp/Tan.Core" = "pytanga/_ga_src/Tan.Core"
```

This copies the entire directory trees. The `_CompileTest_*.cpp` test files and per-module
`CMakeLists.txt` files are also copied, but they are harmless dead weight (~40 KB for the
test files).

**Alternative — explicit file lists (more precise but more maintenance):**

Instead of copying entire directories, list each file explicitly:

```toml
"cpp/Tan.GA/Algo.h" = "pytanga/_ga_src/Tan.GA/Algo.h"
"cpp/Tan.GA/BasisE3.h" = "pytanga/_ga_src/Tan.GA/BasisE3.h"
…  # 45+ entries
```

Recommendation: use directory-level force-include for simplicity. The extra test files are
small and harmless.

### Step 2: Rename `[build]` → `[compile]` optional-dependencies

**File:** `pyproject.toml`

Change:

```toml
# Before
[project.optional-dependencies]
build = [
    "pybind11>=2.11",
    "cmake>=3.18",
    "ninja",
]

# After
[project.optional-dependencies]
compile = [
    "pybind11>=2.11",
    "cmake>=3.18",
    "ninja",
]
```

Also update `all` if it exists (check current pyproject.toml) and any references in
`[dependency-groups]` (e.g., `dev` group references `pytanga[build]`).

Users then do: `pip install pytanga[compile]`

### Step 3: Move CMakeLists.txt into the package

**New file:** `py/pytanga/codegen/CMakeLists.txt`

Copy `py/cmake/binding/CMakeLists.txt` → `py/pytanga/codegen/CMakeLists.txt`.

The content is identical — it takes all paths via `-D` flags (`TANGA_SOURCE`, `BINDING_CPP`,
`MODULE_NAME`), so no logic changes are needed. It just needs to be accessible from the
installed package.

**After this step, `py/cmake/binding/CMakeLists.txt` can optionally be deleted.**
The sdist already includes `/py` so the old location would be bundled, but it's harmless.
Recommend keeping it during the transition and removing in a follow-up cleanup.

### Step 4: Update `_build.py` to use `__file__`-relative paths

**File:** `py/pytanga/codegen/_build.py`

**Before (current logic):**
```python
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
TANGA_SOURCE = Path(
    os.environ.get("PYTANGA_TANGA_SOURCE", _REPO_ROOT / "cpp")
).resolve()
_BINDING_CMAKE = (
    Path(__file__).parent.parent.parent / "cmake" / "binding" / "CMakeLists.txt"
)
```

**After (proposed):**
```python
_HERE = Path(__file__).resolve().parent  # …/pytanga/codegen/

# 1. Bundled source directory (exists in installed wheel)
_BUNDLED_GA_SRC = _HERE.parent / "_ga_src"  # …/pytanga/_ga_src/

# 2. Repo-relative fallback (exists when running from a git checkout)
_REPO_ROOT = _HERE.parent.parent.parent.parent  # 4 levels up from codegen/
_REPO_CPP = _REPO_ROOT / "cpp"

# Resolve TANGA_SOURCE: env var → bundled → repo fallback
_tanga_source_raw = os.environ.get("PYTANGA_TANGA_SOURCE")
if _tanga_source_raw:
    TANGA_SOURCE = Path(_tanga_source_raw).resolve()
elif _BUNDLED_GA_SRC.is_dir():
    TANGA_SOURCE = _BUNDLED_GA_SRC
else:
    TANGA_SOURCE = _REPO_CPP

# CMakeLists.txt is inside the codegen package
_CMAKE_SOURCE_DIR = _HERE  # …/pytanga/codegen/ (contains CMakeLists.txt)
```

**Changes in `build_binding()`:**
- Remove the separate `_find_cmake()`, `_find_ninja()`, `_find_gxx()` logic (keep if already refactored)
- Update the cmake `-S` flag from `str(_BINDING_CMAKE.parent)` to `str(_CMAKE_SOURCE_DIR)`
- The `TANGA_SOURCE` parameter already flows through — no changes to the cmake invocation

### Step 5: Remove dead `_template.cpp` references

**File:** `pyproject.toml`

Remove the force-include line:
```toml
# Remove this line
"py/pytanga/_template.cpp" = "pytanga/_template.cpp"
```

**File:** `py/pytanga/codegen/_cache.py`

Remove lines 45–47:
```python
# Remove these lines
# Content of the binding template
template = Path(__file__).parent.parent / "_template.cpp"
h.update(template.read_bytes())
```

**File:** `py/pytanga/_template.cpp` (optional)

Can be deleted or left with a `# LEGACY: unused` comment. Recommendation: delete it
since it's dead code and the generated code in `_generator.py._emit()` is the active
code path.

### Step 6: Update documentation

Two documentation files need updating to reflect the new installation workflow.

#### 6a. `README.md`

**Current state:** No installation instructions at all — just a one-line description.

**Add a "Quick Start" section after the description:**

```markdown
## Quick Start

### Install as a dependency (recommended for users)

```bash
pip install pytanga[compile]
```

The `[compile]` extra installs pybind11, cmake, and ninja — the tools needed for
on-the-fly C++ compilation. The first time you use an algebra, pytanga compiles the
binding (~5 seconds) and caches the result in `~/.cache/pytanga/`. Subsequent imports
are instant.

System prerequisites: a C++20 compiler (g++ or clang).

### Install for development

```bash
git clone https://github.com/dodeka12/tanga.git
cd tanga
pip install -e ".[compile,dev]"
```

In editable/development mode, `_build.py` automatically finds the C++ sources at
`cpp/` in the repo root — no extra configuration needed.
```

#### 6b. `docs/py/index.md`

**Changes needed:**

1. **Line 28:** `pip install pytanga[build]` → `pip install pytanga[compile]`
2. **Line 65:** `pip install -e ".[build,test]"` → `pip install -e ".[compile,dev]"`
3. **Line 4–6 (first paragraph):** The line "No pre-compiled wheels or system-level installations required — a C++ compiler, cmake, ninja, and pybind11 are the only prerequisites." should be updated to clarify that these come via the `[compile]` extra:

   ```markdown
   **Zero-dependency geometric algebra** with **just-in-time compiled Python bindings**.
   The C++ TanGA library is compiled on-demand into a Python extension module via pybind11.
   Install with `pip install pytanga[compile]` to pull in the build tools (cmake, ninja, pybind11).
   A C++20 compiler (g++ or clang) must be installed separately on your system.
   ```

4. **Add a new short section** distinguishing the two workflows:

   ```markdown
   ### Installation as a Library vs. Development

   | Scenario | Command | C++ Sources From |
   |----------|---------|------------------|
   | Use pytanga in your project | `pip install pytanga[compile]` | Bundled in the wheel (`pytanga/_ga_src/`) |
   | Develop pytanga itself | `git clone … && pip install -e ".[compile,dev]"` | Repo `cpp/` directory |
   | Custom C++ sources | `PYTANGA_TANGA_SOURCE=/path/to/cpp pip install pytanga[compile]` | Environment variable override |
   ```

5. **Remove the repo layout tree (lines 68–90)** from the Quick Start / Development section — it's noise for users who install from a wheel. Move it to `docs/dev/README.md` instead (the development docs).

6. **`docs/dev/README.md`:** Add the repo layout tree here (moved from `docs/py/index.md`) since it's only relevant for developers.

### Step 7: Verify the changes
### Step 5: Remove dead `_template.cpp` references

**File:** `pyproject.toml`

Remove the force-include line:
```toml
# Remove this line
"py/pytanga/_template.cpp" = "pytanga/_template.cpp"
```

**File:** `py/pytanga/codegen/_cache.py`

Remove lines 45–47:
```python
# Remove these lines
# Content of the binding template
template = Path(__file__).parent.parent / "_template.cpp"
h.update(template.read_bytes())
```

**File:** `py/pytanga/_template.cpp` (optional)

Can be deleted or left with a `# LEGACY: unused` comment. Recommendation: delete it
since it's dead code and the generated code in `_generator.py._emit()` is the active
code path.

### Step 6: Update documentation

Two documentation files need updating to reflect the new installation workflow.

#### 6a. `README.md`

**Current state:** No installation instructions at all — just a one-line description.

**Add a "Quick Start" section after the description:**

```markdown
## Quick Start

### Install as a dependency (recommended for users)

```bash
pip install pytanga[compile]
```

The `[compile]` extra installs pybind11, cmake, and ninja — the tools needed for
on-the-fly C++ compilation. The first time you use an algebra, pytanga compiles the
binding (~5 seconds) and caches the result in `~/.cache/pytanga/`. Subsequent imports
are instant.

System prerequisites: a C++20 compiler (g++ or clang).

### Install for development

```bash
git clone https://github.com/dodeka12/tanga.git
cd tanga
pip install -e ".[compile,dev]"
```

In editable/development mode, `_build.py` automatically finds the C++ sources at
`cpp/` in the repo root — no extra configuration needed.
```

#### 6b. `docs/py/index.md`

**Changes needed:**

1. **Line 28:** `pip install pytanga[build]` → `pip install pytanga[compile]`
2. **Line 65:** `pip install -e ".[build,test]"` → `pip install -e ".[compile,dev]"`
3. **Line 4–6 (first paragraph):** The line "No pre-compiled wheels or system-level installations required — a C++ compiler, cmake, ninja, and pybind11 are the only prerequisites." should be updated to clarify that these come via the `[compile]` extra:

   ```markdown
   **Zero-dependency geometric algebra** with **just-in-time compiled Python bindings**.
   The C++ TanGA library is compiled on-demand into a Python extension module via pybind11.
   Install with `pip install pytanga[compile]` to pull in the build tools (cmake, ninja, pybind11).
   A C++20 compiler (g++ or clang) must be installed separately on your system.
   ```

4. **Add a new short section** distinguishing the two workflows:

   ```markdown
   ### Installation as a Library vs. Development

   | Scenario | Command | C++ Sources From |
   |----------|---------|------------------|
   | Use pytanga in your project | `pip install pytanga[compile]` | Bundled in the wheel (`pytanga/_ga_src/`) |
   | Develop pytanga itself | `git clone … && pip install -e ".[compile,dev]"` | Repo `cpp/` directory |
   | Custom C++ sources | `PYTANGA_TANGA_SOURCE=/path/to/cpp pip install pytanga[compile]` | Environment variable override |
   ```

5. **Remove the repo layout tree (lines 68–90)** from the Quick Start / Development section — it's noise for users who install from a wheel. Move it to `docs/dev/README.md` instead (the development docs).

6. **`docs/dev/README.md`:** Add the repo layout tree here (moved from `docs/py/index.md`) since it's only relevant for developers.

### Step 7: Verify the changes

1. **Build a wheel and inspect it:**
   ```bash
   pip install build
   python -m build --wheel
   unzip -l dist/pytanga-*.whl | grep "_ga_src"
   ```
   Expected: `pytanga/_ga_src/Tan.GA/…`, `pytanga/_ga_src/Tan.Math/…`, `pytanga/_ga_src/Tan.Core/…`

2. **Install the wheel and test compilation:**
   ```bash
   pip install dist/pytanga-*.whl[compile]
   python -c "
   from pytanga.codegen._build import TANGA_SOURCE
   print('TANGA_SOURCE:', TANGA_SOURCE)
   print('is_dir:', TANGA_SOURCE.is_dir())
   "
   ```
   Expected: `TANGA_SOURCE` points to `…/pytanga/_ga_src/` and is a directory.

3. **Test from repo checkout (dev mode):**
   ```bash
   pip install -e ".[compile]"
   python -c "
   from pytanga.codegen._build import TANGA_SOURCE
   print('TANGA_SOURCE:', TANGA_SOURCE)
   "
   ```
   Expected: `TANGA_SOURCE` points to `<repo>/cpp/` (the repo fallback).

4. **Test with env var override:**
   ```bash
   PYTANGA_TANGA_SOURCE=/some/other/path python -c "
   from pytanga.codegen._build import TANGA_SOURCE
   print('TANGA_SOURCE:', TANGA_SOURCE)
   "
   ```
   Expected: `TANGA_SOURCE` is `/some/other/path`.

5. **Run the existing test suite:**
   ```bash
   pytest py/tests/
   ```

---

## What Does NOT Change

| Concern | Status |
|---------|--------|
| `cpp/` directory location | Stays at repo root — not moved |
| C++ build system (`cpp/*/CMakeLists.txt`) | Untouched |
| sdist (`/cpp` already included) | Continues to work |
| `_cache.py` cache key computation | Still hashes all `.h` files under `TANGA_SOURCE`, plus all `.py` in `codegen/` |
| `_generator.py` | Unchanged — still emits `#include <Tan.GA/…>` with angle brackets |
| `TANGA_SOURCE` env var override | Still works — always wins |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `force-include` of entire directories copies test `.cpp` files and `CMakeLists.txt` | High (happens by design) | Harmless — unused files in the wheel, ~40 KB extra. Acceptable. |
| `_CompileTest_*.cpp` files could interfere with CMake globbing | Low | CMakeLists.txt uses explicit file lists (`set(TANGA_IMPL_SRCS …)`, not `GLOB`. No risk. |
| Angle-bracket includes (`<Tan.GA/…>`) break if include path is wrong | Low | `_build.py` passes `-DTANGA_SOURCE_DIR=<path>` to cmake, and CMakeLists.txt does `target_include_directories(… PRIVATE "${TANGA_SOURCE}")`. `TANGA_SOURCE` is `_ga_src/` which contains `Tan.GA/`, `Tan.Math/`, `Tan.Core/`. Correct. |
| Zip-safe wheels break `Path(__file__).parent` file access | Very low | hatchling produces non-zip-safe directory installs by default. |
| Cache key changes after removing `_template.cpp` from hash | None (by design) | Existing caches will miss and recompile. One-time cost. Acceptable. |
| `_ga_src/` directory gets picked up by Python's package discovery | Low | `_ga_src/` has no `__init__.py` and contains only `.h`/`.cpp` files. Not importable. Harmless. |
| Tan.Core/Array.cpp is excluded but `Array.h` has inline implementations | Verify | Check: `Array.h` is header-only (all template/inline). `Array.cpp` contains explicit instantiations — not needed for the binding since the Multivector types use different template parameters. Safe to exclude. |

---

## Implementation Order

| Step | File(s) | Description | Effort | Depends on |
|------|---------|-------------|--------|------------|
| 1 | `pyproject.toml` | Add `force-include` for `cpp/Tan.GA`, `cpp/Tan.Math`, `cpp/Tan.Core` | 5 min | — |
| 2 | `pyproject.toml` | Rename `[build]` → `[compile]`, update `[dependency-groups]` | 5 min | — |
| 3 | `py/pytanga/codegen/CMakeLists.txt` (new) | Copy from `py/cmake/binding/CMakeLists.txt` | 2 min | — |
| 4 | `py/pytanga/codegen/_build.py` | Replace `_REPO_ROOT` with `__file__`-relative + fallback | 15 min | 1 |
| 5 | `pyproject.toml` + `py/pytanga/codegen/_cache.py` + `py/pytanga/_template.cpp` | Remove dead template references | 5 min | — |
| 6 | `README.md`, `docs/py/index.md`, `docs/dev/README.md` | Update installation docs for both user and dev workflows | 20 min | — |
| 7 | — | Build wheel, install, verify (see Step 7 above) | 20 min | 1–6 |

**Total: ~70 minutes.**

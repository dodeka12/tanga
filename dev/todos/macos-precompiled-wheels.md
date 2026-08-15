# macOS Compilation & Precompiled Wheel Support

**Created:** 2026-08-14 | **Status:** Planned

## Overview

This repo compiles algebra bindings on demand via a CMake + C++17 toolchain
(`py/pytanga/codegen/_build.py`) and precompiles a fixed set of algebras for
wheel packaging (`tools/build-precompiled.py`). Precompiled wheels currently
exist only for Linux and Windows. This plan covers:

1. **Part A** — what to install on this machine (Intel macOS) to enable the
   local on-demand / precompiled compilation path.
2. **Part B** — C++ source fixes required to compile under **Apple Clang /
   libc++** (affects both Intel and Apple Silicon macOS).
3. **Part C** — C++ source fixes required specifically for **arm64 / Apple
   Silicon** (x86 intrinsics and flags).
4. **Part D** — CI changes to add two macOS build paths (Intel `x86_64` +
   Apple Silicon `arm64`) to the `publish.yml` runner matrix.

> Scope note: this document is a plan only. No code changes have been made yet.

---

## Current State

### This machine (verified 2026-08-14)

| Tool | Status | Notes |
|------|--------|-------|
| Architecture | `x86_64` (Intel) | `uname -m` |
| C++ compiler | ✅ `Apple clang 14.0.0` | active dev dir `/Library/Developer/CommandLineTools` |
| GNU Make | ✅ 3.81 | fallback CMake generator only |
| `cmake` | ✅ available via `uv run` | first installed into the `uv` env |
| `ninja` | ✅ available via `uv run` | |
| `pybind11` | ✅ available via `uv run` | |
| `uv` | ✅ 0.12.4 | |
| `python3` | ⚠️ 3.9.6 (system) | too old; `requires-python = ">=3.12"` |
| `.python-version` | `3.12.12` | `uv` resolves this automatically |

### Repo build flow (confirmed)

`tools/build-precompiled.py` → `pytanga.codegen._cache.get_or_build()` →
`_build.py` → **CMake** + **C++17** + **pybind11** (+ Ninja if present).

The compile-time Python packages are declared in the `[compile]` extra in
`pyproject.toml`:

```toml
[project.optional-dependencies]
compile = [
    "pybind11>=2.11",
    "cmake>=3.18",
    "ninja",
]
```

and the `dev` group pulls in `tanga-py[compile,examples,galgebra]`.

### Current CI (`.github/workflows/publish.yml`)

- `build-pure` — pure Python wheel (no compiled extensions).
- `build-linux` — manylinux x86_64, matrix `python-version: ["3.12", "3.13"]`.
- `build-windows` — `windows-latest`, MSVC, matrix `["3.12", "3.13"]`.
- `build-macos` — **commented out**, with the note:
  `# -- macOS build disabled until precompiled compilation is fixed --`.

### Why the local wheel build currently fails (observed 2026-08-14)

Even with `cmake`/`ninja`/`pybind11` present, `uv run python tools/build-precompiled.py`
fails during the very first algebra (E2). Apple Clang + libc++ reports two
distinct source-level errors:

1. **`cpp/Tan.Core/StrideIterator.h:47/219` — ambiguous `std::random_access_iterator_tag`.**
   The file manually forward-declares the tag inside `namespace std`
   (lines 29–32), which collides with libc++'s definition under its inline
   namespace (`std::__1::random_access_iterator_tag`), making the typedef ambiguous.

2. **`cpp/Tan.Math/Matrix.h:837/863` — `` `this` cannot be implicitly captured ``.**
   The `IsNumber()` / `IsFiniteNumber()` member templates pass non-capturing
   lambdas to `ForEachCompTest`, and the unqualified `IsNumber(tValue)` /
   `IsFiniteNumber(tValue)` calls require `this` from inside the lambda.

These are portability issues, not packaging issues: the wheel build only
"does not work" because the precompiled `.so` generation step does not compile
under Apple Clang. Fixes are detailed in Part B below.

---

## Part A — Install on this Intel Mac

No OS-level packages are required beyond the compiler (already present). The
only extra pieces are Python packages from the `[compile]` extra.

### A1. Install the compile toolchain

```bash
# Preferred: sync the full dev environment (matches CI)
uv sync --group dev

# Or, install just the compile extra into the project env
uv pip install 'tanga-py[compile]'
```

This installs **cmake**, **ninja**, and **pybind11**; `uv run` puts them on
`PATH`. `uv` will also fetch the managed Python 3.12 interpreter that
`.python-version` pins.

### A2. Verify

```bash
uv run cmake --version      # >= 3.18
uv run ninja --version
uv run python -c "import pybind11; print(pybind11.get_cmake_dir())"
uv run python --version     # 3.12.x (not the system 3.9.6)
```

### A3. Compile + wheel smoke test (depends on Part B)

```bash
uv run python tools/build-precompiled.py
uv build --wheel -o /tmp/tanga-dist
uv run python tools/fix-wheel-tag.py -d /tmp/tanga-dist
```

Expected result after Part B is applied: seven precompiled `.so` extensions in
`precompiled/`, and a wheel tagged `...cp312-cp312-macosx_<ver>_0_x86_64.whl`.

> **Note:** `uv build --wheel` itself already succeeds (`tanga_py-0.9.2-py3-none-any.whl`);
> it is the `build-precompiled.py` step above it that fails until Part B is done.

---

## Part B — Apple Clang / libc++ portability fixes (Intel **and** Apple Silicon)

These fixes are required for compilation on both Intel Macs and Apple Silicon
Macs (anything using Apple Clang + libc++). They are independent of the
arm64-specific fixes in Part C.

### B1. `cpp/Tan.Core/StrideIterator.h` — remove the `std` forward declaration

**File:** `cpp/Tan.Core/StrideIterator.h`, lines 29–32 and 47 / 219.

Current code manually forward-declares the iterator tag:

```cpp
namespace std
{
	struct random_access_iterator_tag;
}
```

This is invalid (it declares into `namespace std`, which is reserved) and
conflicts with libc++'s real `std::__1::random_access_iterator_tag`, producing:

```
error: reference to 'random_access_iterator_tag' is ambiguous
```

**Required change:** delete the manual `namespace std { ... }` block and rely on
a proper include so the real tag is visible to the two `typedef` lines
(`CStrideIterator` line 47 and `CStrideIteratorConst` line 219):

- Add `#include <iterator>` near the top of the file (after the existing
  `#include "Defines.h"`), and
- Remove the forward-declaration block (lines 29–32).

### B2. `cpp/Tan.Math/Matrix.h` — fix lambda `this` capture in `IsNumber`/`IsFiniteNumber`

**File:** `cpp/Tan.Math/Matrix.h`

- `IsNumber()` member template, line 837.
- `IsFiniteNumber()` member template, line 863.

Current:

```cpp
return ForEachCompTest([](const TValue& tValue)
{
    if (!IsNumber(tValue))
    {
        return false;
    }
    return true;
});
```

Under Apple Clang the unqualified `IsNumber(tValue)` is resolved against the
enclosing member function, requiring `this` from inside a non-capturing lambda:

```
error: 'this' cannot be implicitly captured in this context
```

**Required change (to be confirmed when implementing):** make the per-element
check explicit and self-contained. Two options:

1. **Minimal:** capture the object explicitly — `[this](const TValue& tValue){ ... }`
   — then use a scalar check that does not depend on an unqualified member call.
2. **Preferred:** call a scalar (non-member) number/finite predicate directly,
   e.g. `std::isfinite(tValue)` for `IsFiniteNumber` and the matching
   `!std::isnan(…)`-style check for `IsNumber`, with no `this` capture.

> **Verification note for the implementer:** the codebase currently defines
> `IsNumber`/`IsFiniteNumber` only for `tvec1..4` and `tvec<T,t_iDim>`
> (in `FixedVectorTypes.h`) and as zero-argument members of `CMatrix`
> (in `Matrix.h`). There is **no scalar `IsNumber(double)` / `IsFiniteNumber(double)`
> overload**. Confirm the intended scalar semantics (modular `int64` algebras
> may differ from `float64`) before choosing the predicate.

---

## Part C — Make the C++ library compile on Apple Silicon (arm64)

These are the x86-only blockers behind the commented-out macOS job. They apply
on top of the Apple-Clang fixes in Part B.

### C1. `cpp/Tan.Core/IntrinsicFunctions.h` — remove unconditional x86 intrinsics

**File:** `cpp/Tan.Core/IntrinsicFunctions.h`

Current code (lines 30–52, 67–70) is MSVC-vs-everything-else, and the
"everything-else" branch hard-codes x86 with no ARM fallback:

```cpp
#ifdef _MSC_VER
#	include <intrin.h>
#	include <nmmintrin.h>
#else
#	include <x86intrin.h>      // ❌ x86-only
#	include <nmmintrin.h>      // ❌ x86-only
	// GCC/Clang _BitScanReverse helpers (portable, use __builtin_clz)
#endif
...
inline unsigned CountOneBits(const unsigned& uValue)
{
	return _mm_popcnt_u32(uValue);   // ❌ x86 intrinsic
}
```

**Required change:**

- Gate the `<x86intrin.h>` / `<nmmintrin.h>` includes on an x86 macro
  (`__x86_64__` / `__i386__`). The arm64 path must include neither.
- Replace `_mm_popcnt_u32(uValue)` with the portable `__builtin_popcount(uValue)`
  in the GCC/Clang (non-MSVC) path. This still emits `popcnt` on x86 when
  `-mpopcnt` is passed, and compiles natively on arm64.
- Keep the MSVC branch (`<intrin.h>` / `_mm_popcnt_u32`) unchanged, since
  `__builtin_popcount` is not available there.

Suggested structure:

```cpp
#ifdef _MSC_VER
#	include <intrin.h>
#	include <nmmintrin.h>
	// ... existing MSVC helpers (no _BitScanReverse shims needed)
#else
#	if defined(__x86_64__) || defined(__i386__)
#		include <x86intrin.h>
#		include <nmmintrin.h>
#	endif
	// _BitScanReverse shims here (already portable via __builtin_clz)
#endif
...
	inline unsigned CountOneBits(const unsigned& uValue)
	{
#	ifdef _MSC_VER
		return _mm_popcnt_u32(uValue);
#	else
		return __builtin_popcount(uValue);
#	endif
	}
```

`IntrinsicFunctions.h` is transitively included by `Blade.h`, `BladeMask.h`,
`SubspaceMask.h`, `Blade_Operators.h`, and `Matrix.Algo.GE.h`, so it must be
fixed before any arm64 translation unit compiles.

### C2. `py/pytanga/codegen/CMakeLists.txt` — gate x86-only compile flags

**File:** `py/pytanga/codegen/CMakeLists.txt`

Current (lines 58–62):

```cmake
if(MSVC)
    target_compile_options(${MODULE_NAME} PRIVATE /bigobj /O2)
else()
    target_compile_options(${MODULE_NAME} PRIVATE -msse4.1 -mpopcnt -O3)
endif()
```

**Required change:** pass `-msse4.1 -mpopcnt` only on x86; on arm64 use `-O3`
without the x86 flags. Example:

```cmake
if(MSVC)
    target_compile_options(${MODULE_NAME} PRIVATE /bigobj /O2)
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64|i[3-6]86")
    target_compile_options(${MODULE_NAME} PRIVATE -msse4.1 -mpopcnt -O3)
else()
    target_compile_options(${MODULE_NAME} PRIVATE -O3)
endif()
```

This is the file that drives wheel precompilation, so it is **mandatory** for
the macOS arm64 wheel build.

### C3. C++ test `CMakeLists.txt` files — guard the same flags

These are only run by the Linux `ci.yml` C++ test target today, but hard-code
the same x86 flags and would break an arm64 C++ test build (e.g. a future macOS
CI test leg). Guard them identically for completeness:

| File | Lines |
|------|-------|
| `cpp/Tan.GA/CMakeLists.txt` | 36–41 |
| `cpp/Tan.Crypt.Test/CMakeLists.txt` | 9–14 |
| `cpp/Tan.App.Test/CMakeLists.txt` | 29–34 |

Each uses:

```cmake
if(MSVC)
    ... /arch:SSE4.1 ...
else()
    ... -msse4.1 ... -mpopcnt ...
endif()
```

Change to an x86-guarded `elseif(...)` / fallback-`else()` (drop the x86 flags
on arm64). Not strictly required for wheel publishing, but necessary for a
fully green macOS CI.

### C4. `py/pytanga/codegen/_build.py` — no change needed (verify only)

The Darwin compiler mapping (`"Darwin": "clang++"`) and the extension suffix
map (`"Darwin": [".so", ".dylib"]`) are already correct. On Apple Silicon,
`platform.machine()` returns `"arm64"`, and `fix-wheel-tag.py` already derives
the platform tag from `platform.machine()` / `platform.mac_ver()`, so no
build-driver or tagging changes are required.

---

## Part D — Add two macOS build paths to the runner matrix

### D1. `publish.yml` — uncomment/replace the `build-macos` job

**File:** `.github/workflows/publish.yml`

Replace the commented-out `build-macos` block (lines 192–220) with a real job
that mirrors `build-windows` but runs on macOS. Matrix:

```yaml
  build-macos:
    name: Build macOS wheel (${{ matrix.os }}, ${{ matrix.python-version }})
    needs: [compute-version]
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [macos-13, macos-14]
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        id: setup-python
        with:
          python-version: ${{ matrix.python-version }}

      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Sync dependencies
        run: uv sync --group dev
        env:
          UV_PYTHON: ${{ steps.setup-python.outputs.python-path }}

      - name: Build precompiled
        run: uv run python tools/build-precompiled.py
        env:
          UV_PYTHON: ${{ steps.setup-python.outputs.python-path }}

      - name: Build wheel and fix tag
        run: |
          SETUPTOOLS_SCM_PRETEND_VERSION="${{ needs.compute-version.outputs.pretend_version }}" \
            uv run bash tools/build-precompiled-wheel.sh
        env:
          UV_PYTHON: ${{ steps.setup-python.outputs.python-path }}

      - uses: actions/upload-artifact@v4
        with:
          name: wheels-macos-${{ matrix.os }}-${{ matrix.python-version }}
          path: dist/*.whl
```

Key points:

- `macos-13` = Intel (`x86_64`), `macos-14` = Apple Silicon (`arm64`), giving
  the two distinct compile paths.
- `Xcode Command Line Tools` (`clang++`) are preinstalled on GitHub macOS
  runners — no compiler setup step is needed.
- Use `actions/setup-python@v5` + `UV_PYTHON` (as in `build-windows`) so each
  matrix cell compiles against the correct `cp312` / `cp313` interpreter and
  overrides the local `.python-version` pin.
- `build-precompiled-wheel.sh` already runs
  `uv build --wheel` and `fix-wheel-tag.py`, which produces the correct
  platform tag (`macosx_13_0_x86_64` vs `macosx_14_0_arm64`).
- `dist/` is job-local, so no filename collision between matrix cells.

### D2. `publish.yml` — add `build-macos` to the publish job's `needs`

**File:** `.github/workflows/publish.yml`, line 224

```yaml
  publish:
    needs: [build-pure, build-linux, build-windows, build-macos]
```

The `download-artifact` step already uses `pattern: wheels-*` with
`merge-multiple: true`, so the new `wheels-macos-*` artifacts are collected
automatically. No other change is required there.

### (Optional) D3. `ci.yml` — add a macOS test leg

Not part of this plan's core scope, but once Parts B+C land, an arm64 macOS
pytest / C++ test leg in `.github/workflows/ci.yml` would prevent regressions.
Defer until Parts A–D are validated.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `random_access_iterator_tag` ambiguous under libc++ | Certain (current state) | B1 remove the invalid `std` forward decl + include `<iterator>` |
| Lambda `this` capture error under Apple Clang | Certain (current state) | B2 explicit capture / scalar predicate |
| No scalar `IsNumber`/`IsFiniteNumber` overload exists | Certain | B2 implementer must confirm intended scalar semantics |
| `-msse4.1`/`-mpopcnt` rejected on arm64 | Certain (current state) | C2/C3 flag guards |
| `x86intrin.h` missing on arm64 | Certain (current state) | C1 architecture-gated includes |
| `_mm_popcnt_u32` missing on arm64 | Certain (current state) | C1 `__builtin_popcount` fallback |
| macOS runner lacks a C++ toolchain | None | `clang++` + Xcode CLT preinstalled on `macos-*` runners |
| Wrong Python picked up (system 3.9) | Low | `actions/setup-python@v5` + `UV_PYTHON` override |
| Wheel tag collision / wrong tag | Low | `fix-wheel-tag.py` derives tag from `platform.machine()`/`mac_ver()` per runner |
| `macos-14` runner is actually arm64 | None | GitHub `macos-14`/`macos-latest` are arm64; `macos-13` is Intel x86_64 |
| C++ test CMake files still x86-only | Medium | C3 covers all three test dirs |

---

## Implementation Order

| Step | File(s) | Effort | Depends on |
|------|---------|--------|------------|
| A1–A2 | install + verify toolchain | 10 min | — |
| B1 | `cpp/Tan.Core/StrideIterator.h` | 10 min | — |
| B2 | `cpp/Tan.Math/Matrix.h` | 20 min | — |
| A3 | local compile + wheel smoke test | 10 min | B1, B2 |
| C1 | `cpp/Tan.Core/IntrinsicFunctions.h` | 20 min | — |
| C2 | `py/pytanga/codegen/CMakeLists.txt` | 10 min | — |
| C3 | `cpp/Tan.GA/CMakeLists.txt`, `cpp/Tan.Crypt.Test/CMakeLists.txt`, `cpp/Tan.App.Test/CMakeLists.txt` | 15 min | — |
| C4 | verify `_build.py` / `fix-wheel-tag.py` (no change) | 5 min | C1, C2 |
| D1 | `publish.yml` — `build-macos` job + matrix | 20 min | B1, B2, C1, C2 |
| D2 | `publish.yml` — `publish.needs` | 5 min | D1 |

**Total: ~125 minutes.**

---

## Verification

### Local (Intel Mac)

1. `uv run python tools/build-precompiled.py` completes and writes 7
   extensions to `precompiled/`.
2. `uv build --wheel -o /tmp/tanga-dist && uv run python tools/fix-wheel-tag.py -d /tmp/tanga-dist`
   produces `tanga_py-*.whl` with a `macosx_*_x86_64` tag.
3. No compiler errors referencing `random_access_iterator_tag` or
   `cannot be implicitly captured`.

### CI (after Part B + C + D)

Trigger a manual `cd.yml` / `publish.yml` run (`workflow_dispatch`) and verify:

1. `build-macos` produces wheels for all four cells:
   - `macos-13` × cp312 → `...cp312-cp312-macosx_13_0_x86_64.whl`
   - `macos-13` × cp313 → `...cp313-cp313-macosx_13_0_x86_64.whl`
   - `macos-14` × cp312 → `...cp312-cp312-macosx_14_0_arm64.whl`
   - `macos-14` × cp313 → `...cp313-cp313-macosx_14_0_arm64.whl`
2. No compiler errors referencing `x86intrin.h`, `_mm_popcnt_u32`,
   `-msse4.1`, or `-mpopcnt` in the `macos-14` (arm64) jobs.
3. `publish` collects `wheels-macos-*` alongside `wheels-linux-*` /
   `wheels-windows-*` and uploads all to Test PyPI.
4. Install the `macosx_14_0_arm64` wheel on an Apple Silicon machine and
   confirm precompiled algebras load without JIT compilation.
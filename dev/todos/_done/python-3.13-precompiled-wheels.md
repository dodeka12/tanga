# Python 3.13 Precompiled Wheel Support

**Created:** 2026-08-09 | **Status:** Planned

## Overview

The GitHub deploy workflow (`publish.yml`) currently builds precompiled wheels
only for Python 3.12. Both the Linux and Windows jobs need to be extended to
also compile and publish wheels for Python 3.13, so users on Python 3.13
receive precompiled bindings without needing a local C++ compiler.

---

## Current State

| Job | Python version | How it's set |
|-----|---------------|--------------|
| `build-linux` | 3.12 only | Hardcoded `cp312` paths in manylinux container (lines 67–68, 88 of `publish.yml`) |
| `build-windows` | 3.12 only | `.python-version` pins `3.12.12`; `uv sync` respects it |
| `build-pure` | any (pure Python) | No compiled extensions — already version-independent |

The `build-precompiled.py` script records `python_abi` (e.g. `cp312`) from the
running interpreter into `manifest.json` and the compiled `.so`/`.pyd`
filenames include ABI tags (e.g. `.cpython-312-x86_64-linux-gnu.so`), so each
build is inherently scoped to a single Python minor version.

`pyproject.toml` declares `requires-python = ">=3.12"`, so 3.13 is supported at
the metadata level — only the CI build matrix is missing.

---

## Implementation Plan

### Step 1 — `publish.yml`: Add Python version matrix to `build-linux`

**File:** `.github/workflows/publish.yml`

Add a matrix strategy over Python versions to the `build-linux` job:

```yaml
  build-linux:
    name: Build Linux wheel (${{ matrix.python-version }}, manylinux_x86_64)
    runs-on: ubuntu-24.04
    container: quay.io/pypa/manylinux_2_28_x86_64
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      ...
```

Update the hardcoded `cp312` references to use the matrix variable. In
manylinux, Python interpreters are at `/opt/python/cp3XX-cp3XX/`. The
`python-version` matrix value can be mapped:

| Matrix value | ABI tag   | Interpreter path                              |
|-------------|-----------|-----------------------------------------------|
| `3.12`      | `cp312`   | `/opt/python/cp312-cp312/bin`                 |
| `3.13`      | `cp313`   | `/opt/python/cp313-cp313/bin`                 |

A bash step (or env interpolation) can derive these from the matrix value:

```bash
ABI="cp${python_version/./}"
PYTHON_BIN="/opt/python/${ABI}-${ABI}/bin"
```

**Changes required:**

1. Add `strategy.matrix.python-version` with `["3.12", "3.13"]`.
2. Replace the hardcoded `echo "/opt/python/cp312-cp312/bin" >> $GITHUB_PATH`
   with a dynamic derivation based on `${{ matrix.python-version }}`.
3. Replace the hardcoded `UV_PYTHON` assignment with the dynamic path.
4. Replace the hardcoded `auditwheel` install/repair commands to use the
   matrix Python's pip.
5. Update the uploaded artifact name to include the Python version (e.g.
   `wheels-linux-cp312`, `wheels-linux-cp313`) so both versions' wheels
   are collected by the publish job.
6. Update the `publish` job's `download-artifact` to use the new artifact
   name pattern (or use `pattern: wheels-linux-*`).

### Step 2 — `publish.yml`: Add Python version matrix to `build-windows`

**File:** `.github/workflows/publish.yml`

Add a matrix strategy over Python versions to the `build-windows` job:

```yaml
  build-windows:
    name: Build Windows wheel (${{ matrix.python-version }}, win_amd64)
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      ...
```

On Windows, changing the Python version is simpler than on Linux because
`uv sync` can be told which Python to use via `UV_PYTHON`. GitHub's
`windows-latest` runners have both 3.12 and 3.13 pre-installed (paths like
`C:\hostedtoolcache\windows\Python\3.12.x\x64` and `3.13.x\x64`).

**Changes required:**

1. Add `strategy.matrix.python-version` with `["3.12", "3.13"]`.
2. Install the specific Python version using `actions/setup-python@v5` with
   the matrix version, or set `UV_PYTHON` to the runner's pre-installed
   Python path for the target version.
3. Upload artifacts with version-specific names (e.g. `wheels-windows-cp312`,
   `wheels-windows-cp313`).
4. Update `fix-wheel-tag.py` step if needed (should already work with the
   active interpreter's ABI tag).

**Note:** `.python-version` currently pins `3.12.12`. For the CI job, we
either need to override this or remove the pin from CI context (e.g.
`uv sync --python $pythonLocation`).

### Step 3 — `publish.yml`: Update `publish` job to collect all artifacts

**File:** `.github/workflows/publish.yml`

The current `publish` job downloads all `wheels-*` artifacts. After adding
the matrix, the artifact names become versioned (e.g. `wheels-linux-cp312`,
`wheels-linux-cp313`, `wheels-windows-cp312`, `wheels-windows-cp313`).

**Changes required:**

1. Update the `download-artifact` pattern to `wheels-*` (should already work
   since all new names still start with `wheels-`).
2. Ensure the `needs` array includes all matrix-generated job names, or use
   the full matrix expansion syntax:
   ```yaml
   needs: [build-pure, build-linux, build-windows]
   ```
   The `needs` list already references the job IDs, not individual matrix
   instances, so this should work automatically — GitHub Actions waits for
   all matrix instances to complete.

### Step 4 — `publish.yml`: Consider concurrent manylinux builds

The manylinux container is large, and running two matrix jobs inside separate
containers could be slow. However, this is the standard approach; we accept
the ~2x increase in build time for the Linux job (which is already the
fastest of the platform builds).

Alternative: run both builds inside a single container job by looping over
the Python versions. This is more complex (need to manage two separate build
runs within one job, handle two sets of artifacts) and less idiomatic for
GitHub Actions. The matrix approach is preferred for clarity and
maintainability.

### Step 5 — `tools/build-precompiled.py`: Verify matrix compatibility

**File:** `tools/build-precompiled.py`

Review that the script works correctly regardless of which Python version
invokes it:

- `sys.version_info` is used for the ABI tag (line 43): `"cp{major}{minor}"` —
  this is correct and will produce `cp312` or `cp313` depending on the
  interpreter.
- The compiled extension filenames include the ABI tag from pybind11's
  build — this is also determined by the Python interpreter used.
- `_detect_compiler()` probes `cl.exe` vs `g++` — unaffected by Python version.

**No changes needed** in the build script itself, but worth a verification
note in the plan.

### Step 6 — Verify `.python-version` handling

**File:** `.python-version`

Currently pins `3.12.12`. For local development this is fine (the repo uses
3.12 as the primary dev Python), but in CI we need the matrix Python to
take precedence.

Options:
1. Remove `.python-version` from the repo and let each CI job specify its
   Python via `actions/setup-python` or `UV_PYTHON`.
2. Keep `.python-version` for local dev but override it in CI via
   `UV_PYTHON` environment variable (uv respects this over `.python-version`).

Option 2 is preferred — add `UV_PYTHON` to the Linux and Windows jobs'
`env` section pointing to the correct interpreter for each matrix value.

For the Linux job, this is already done (line 68 of `publish.yml` sets
`UV_PYTHON`) — just make it dynamic.
For the Windows job, add `UV_PYTHON` pointing to the matrix Python.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Manylinux container doesn't have Python 3.13 | Low | `manylinux_2_28_x86_64` is regularly updated; 3.13 has been available since late 2024. Verify before deploying. |
| Windows runner doesn't have Python 3.13 pre-installed | Very low | `windows-latest` (Windows Server 2025) includes Python 3.13. Use `actions/setup-python@v5` as fallback. |
| Binary incompatibility between cp312 and cp313 extensions | None | Each Python version gets its own compiled extensions with the correct ABI tag. pybind11 handles ABI differences. |
| Wheel tag collision (both cp312 and cp313 wheels in same dir) | None | `dist/` is job-local; each matrix instance uploads its own artifact. The publish job merges all artifacts into one `dist/` for upload. |
| Increased CI time | Medium | Two parallel matrix jobs per platform instead of one. Still within GitHub Actions free tier limits for public repos. |
| Auditwheel / fix-wheel-tag compatibility with 3.13 | Low | Both tools support Python 3.13. Verify during first RC build. |

---

## Implementation Order

| Step | File(s) | Effort | Depends on |
|------|---------|--------|------------|
| 1 | `publish.yml` — Linux matrix | 20 min | — |
| 2 | `publish.yml` — Windows matrix | 15 min | — |
| 3 | `publish.yml` — publish job artifact collection | 5 min | 1, 2 |
| 4 | (verification only) | — | — |
| 5 | `tools/build-precompiled.py` — review (no changes expected) | 5 min | — |
| 6 | `.python-version` — CI override strategy | 5 min | 1, 2 |

**Total: ~50 minutes.**

---

## Verification

After implementation, trigger a manual `cd.yml` run (`workflow_dispatch`) and
verify:

1. Both `build-linux` jobs (3.12 and 3.13) complete successfully.
2. Both `build-windows` jobs (3.12 and 3.13) complete successfully.
3. The publish job collects all 4 precompiled wheels + 1 pure wheel.
4. Uploaded wheels to Test PyPI contain correct ABI tags:
   - Linux: `cp312-cp312-manylinux_2_28_x86_64` and `cp313-cp313-manylinux_2_28_x86_64`
   - Windows: `cp312-cp312-win_amd64` and `cp313-cp313-win_amd64`
5. Install the cp313 wheels on a Python 3.13 environment and verify
   precompiled algebras load without JIT compilation.
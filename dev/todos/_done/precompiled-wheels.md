# Pre-Compiled Wheels — Distribute `.so` Binaries for Common Algebras

**Created:** 2026-07-27 | **Status:** Planning

## Problem

Today, every user who wants to use pytanga must install a C++ compiler plus
`cmake`, `ninja`, and `pybind11` (via the `[compile]` extra). The first
import of an `Algebra` triggers a 5–20 second compilation step. For most
Python users — especially on a single platform using common algebras like
E3, P3, N3, PGA3 — this is unnecessary friction.

## Goal

Ship platform-specific wheels containing **pre-compiled `.so` files** for
the four common algebras (E3, P3, N3 / PGA3) with `float64` dtype. Users on
supported platforms can then `pip install pytanga` without a C++ compiler or
the `[compile]` extras.

---

## Design

### Core Strategy: Build-Time Precompilation + Runtime Discovery

Three parts:

1. **A build script** (run manually, later in CI) triggers JIT compilation for
   a fixed list of algebras, harvests the `.so` files, and places them into
   `py/pytanga/precompiled/` before building the wheel.

2. **A runtime loader** in `_cache.py` checks `precompiled/` before falling
   through to JIT compilation — full backward compatibility with the existing
   cache and compile pipeline.

3. **Platform-specific wheels** — once precompiled `.so` files are bundled,
   the wheel can no longer be `py3-none-any`; it becomes e.g.
   `cp312-manylinux_x86_64`.

### Algebra Mapping

P3 and PGA3 share the same `(dim=4, sig=0b1000)` C++ binding — they differ
only in the Python API layer (`BasisP3` vs `BasisPGA3`). Only **five**
unique `.so` files are needed:

| Algebra | dim | sig | dtype | Module Name | Notes |
|---------|-----|-----|-------|-------------|-------|
| E3      | 3   | 0   | float64 | `binding_dim3_sig0_float64` | Standard Euclidean 3D |
| P3 / PGA3 | 4 | 8 | float64 | `binding_dim4_sig8_float64` | Projective / Plane-based 3D |
| N3      | 5   | 16  | float64 | `binding_dim5_sig16_float64` | Null / Conformal 3D |
| E3 (mod) | 3 | 0 | int64 | `binding_dim3_sig0_int64` | Modular arithmetic for crypto |
| Sparse | 10  | 0   | int64 | `binding_dim10_sig0_int64` | High-dim sparse for crypto |

### Precompiled Manifest

`py/pytanga/precompiled/manifest.json`:

```json
{
  "version": 1,
  "platform": "manylinux_2_35_x86_64",
  "python_abi": "cp312",
  "compiler": "g++ (GCC) 13.2.0",
  "algebras": {
    "binding_dim3_sig0_float64":    {"dim": 3, "sig": 0,  "dtype": "float64"},
    "binding_dim4_sig8_float64":    {"dim": 4, "sig": 8,  "dtype": "float64"},
    "binding_dim5_sig16_float64":   {"dim": 5, "sig": 16, "dtype": "float64"},
    "binding_dim3_sig0_int64":      {"dim": 3, "sig": 0,  "dtype": "int64"},
    "binding_dim10_sig0_int64":     {"dim": 10,"sig": 0,  "dtype": "int64"}
  }
}
```

The manifest records platform/ABI/compiler metadata so the runtime loader
can verify compatibility before loading a `.so`.

### Runtime Loader Flow (`_cache.py`)

```
get_or_build(dim, sig, dtype):

  1. PRE-COMPILED CHECK (NEW):
     - Read precompiled/manifest.json (if it exists)
     - If (dim, sig, dtype) matches an entry AND the .so file exists:
       - Compute the cache hex key (existing _make_key logic)
       - If the key matches (headers haven't changed):
         - Copy .so into cache dir under the hex key
         - Write meta.json
         - Load and return
       - If key mismatch: skip precompiled → fall through to compile
     - If manifest or .so is missing/incompatible → continue

  2. CACHE CHECK (existing):
     - Same as today

  3. COMPILE (existing):
     - Same as today (requires cmake/ninja/g++)
```

The **key match** check is critical: if the bundled `.so` was compiled against
a different version of the C++ headers than what's in the current wheel, the
precompiled binary is skipped and the system falls through to JIT compilation.
This is self-healing — users with a compiler always get correct behavior.

### Wheel Distribution Strategy

| Wheel Tag | Contents | Audience |
|-----------|----------|----------|
| `py3-none-any` | Pure Python + C++ headers, no precompiled | Users with compiler (today's wheel) |
| `cp312-manylinux_x86_64` | + precompiled .so for E3/P3/N3/PGA3 | Linux x86_64 users without compiler |
| `cp312-macosx_arm64` | + precompiled .dylib | macOS Apple Silicon users |

pip automatically selects the most specific wheel (platform wheel over pure
wheel). Users on unsupported platforms still get the pure wheel and can use
`[compile]` as before.

---

## Implementation Steps

### Step 1: Create Build Script

**New file:** `tools/build-precompiled.py`

A Python script that:

1. Imports pytanga and triggers compilation for each algebra
2. Harvests the resulting `.so` files from `~/.cache/pytanga/<key>/`
3. Copies them into `py/pytanga/precompiled/`
4. Writes `manifest.json` with platform detection

```python
#!/usr/bin/env python3
"""Build precompiled bindings for common algebras and bundle into the package."""
from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path

ALGEBRAS = [
    # (dim, sig, dtype, description)
    (3, 0, "float64", "E3"),
    (4, 8, "float64", "P3/PGA3"),
    (5, 16, "float64", "N3"),
    (3, 0, "int64", "E3 (modular)"),
    (10, 0, "int64", "Sparse high-dim"),
]

REPO_ROOT = Path(__file__).resolve().parent.parent
PRECOMPILED_DIR = REPO_ROOT / "py" / "pytanga" / "precompiled"


def main() -> int:
    import pytanga.codegen._cache as cache_mod
    import pytanga.codegen._build as build_mod

    PRECOMPILED_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "version": 1,
        "platform": platform.platform(),
        "python_abi": f"cp{sys.version_info.major}{sys.version_info.minor}",
        "compiler": _detect_compiler(),
        "algebras": {},
    }

    for dim, sig, dtype, desc in ALGEBRAS:
        print(f"Compiling {desc} (dim={dim}, sig={sig}, dtype={dtype})...")
        try:
            pytanga.get_or_build(dim, sig, dtype, verbose=False)
        except ImportError:
            pass  # already imported, or compiled

        # Find the .so in cache
        from pytanga.codegen._generator import module_name
        mod_name = module_name(dim, sig, dtype)
        cache_root = cache_mod.cache_root()

        # Walk cache dirs looking for the matching .so
        for cache_dir in cache_root.iterdir():
            if not cache_dir.is_dir():
                continue
            meta_path = cache_dir / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            if meta.get("module_name") == mod_name:
                so_path = cache_dir / meta["so_path"]
                if so_path.is_file():
                    dest = PRECOMPILED_DIR / so_path.name
                    shutil.copy2(so_path, dest)
                    manifest["algebras"][mod_name] = {
                        "dim": dim,
                        "sig": sig,
                        "dtype": dtype,
                    }
                    print(f"  → bundled {so_path.name}")
                break

    # Write manifest
    manifest_path = PRECOMPILED_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to {manifest_path}")
    print(f"Precompiled .so files in {PRECOMPILED_DIR}:")
    for f in sorted(PRECOMPILED_DIR.iterdir()):
        print(f"  {f.name}")

    return 0


def _detect_compiler() -> str:
    import subprocess
    try:
        out = subprocess.run(
            ["g++", "--version"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.splitlines()[0] if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 2: Add `force-include` for Precompiled Directory

**File:** `pyproject.toml`

Add one line to the existing force-include section:

```toml
[tool.hatch.build.targets.wheel.force-include]
"cpp/Tan.GA"   = "pytanga/_ga_src/Tan.GA"
"cpp/Tan.Math" = "pytanga/_ga_src/Tan.Math"
"cpp/Tan.Core" = "pytanga/_ga_src/Tan.Core"
"py/pytanga/precompiled" = "pytanga/precompiled"   # ← NEW
```

If the `precompiled/` directory doesn't exist (e.g. when building a pure
wheel), hatchling silently skips the force-include entry. No conditional
logic needed.

### Step 3: Create Cleanup Script

**New file:** `tools/clean-precompiled.py`

A simple script that removes the `precompiled/` directory so that
subsequent `uv build --wheel` produces a pure `py3-none-any` wheel again.

```python
#!/usr/bin/env python3
"""Remove precompiled bindings to restore a pure-Python wheel build."""
from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRECOMPILED_DIR = REPO_ROOT / "py" / "pytanga" / "precompiled"


def main() -> int:
    if not PRECOMPILED_DIR.exists():
        print(f"Nothing to clean — {PRECOMPILED_DIR} does not exist.")
        return 0

    shutil.rmtree(PRECOMPILED_DIR)
    print(f"Removed {PRECOMPILED_DIR}")
    print("Next 'uv build --wheel' will produce a pure py3-none-any wheel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 4: Add `.gitignore` Entries

**File:** `.gitignore`

```
# Precompiled bindings (build artifact, not tracked)
py/pytanga/precompiled/
```

The precompiled `.so` files are platform-specific build artifacts. They
should never be committed to the repository.

### Step 5: Add Runtime Loader to `_cache.py`

**File:** `py/pytanga/codegen/_cache.py`

Add a `_load_precompiled(dim, sig, dtype, key, entry_dir)` function called
from `get_or_build()` before the cache hit check:

```python
def _load_precompiled(
    dim: int, sig: int, dtype: str, key: str, entry_dir: Path
):
    """Try to use a precompiled .so from pytanga/precompiled/.

    Returns the loaded module on success, or None if no matching
    precompiled binary exists (or if it is incompatible).
    """
    precompiled_dir = Path(__file__).parent.parent / "precompiled"
    manifest_path = precompiled_dir / "manifest.json"

    if not manifest_path.exists():
        return None

    manifest = json.loads(manifest_path.read_text())
    mod_name = mk_module_name(dim, sig, dtype)
    entry = manifest.get("algebras", {}).get(mod_name)

    if entry is None:
        return None

    so_path = precompiled_dir / f"{mod_name}.so"  # .so on Linux, .pyd on Windows
    if not so_path.exists():
        return None

    # Precompiled key — the cache key computed when the .so was built.
    # If the current source headers differ from when the precompiled .so
    # was built, skip it and fall through to JIT compilation.
    precompiled_key = entry.get("key", "")
    if precompiled_key and precompiled_key != key:
        return None

    # Copy into cache so subsequent imports use the cache path
    try:
        shutil.copy2(so_path, entry_dir / f"{mod_name}.so")
        rel_so = Path(f"{mod_name}.so")
        meta = {
            "dim": dim,
            "sig": sig,
            "dtype": dtype,
            "key": key,
            "module_name": mod_name,
            "so_path": rel_so.as_posix(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "precompiled",
        }
        (entry_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    except OSError:
        return None

    return _load(entry_dir / f"{mod_name}.so", mod_name)
```

And modify `get_or_build()` to call this before the cache check:

```python
def get_or_build(dim, sig, dtype, *, verbose=False):
    so_path = lookup(dim, sig, dtype)
    mod_name = mk_module_name(dim, sig, dtype)

    if so_path is not None:
        return _load(so_path, mod_name)

    key = _make_key(dim, sig, dtype)
    entry = cache_root() / key
    entry.mkdir(parents=True, exist_ok=True)

    # --- Precompiled check (NEW) ---
    # Try to use a pre-bundled .so before falling through to compilation
    try:
        module = _load_precompiled(dim, sig, dtype, key, entry)
        if module is not None:
            return module
    except Exception:
        pass  # precompiled load failed → compile normally
    # --- End precompiled check ---

    module, so_path = build_and_load(
        dim, sig, dtype, build_dir=entry,
        tanga_source=TANGA_SOURCE, verbose=verbose,
    )

    rel_so = so_path.relative_to(entry)
    meta = {
        "dim": dim, "sig": sig, "dtype": dtype,
        "key": key, "module_name": mod_name,
        "so_path": rel_so.as_posix(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (entry / "meta.json").write_text(json.dumps(meta, indent=2))
    return module
```

### Step 5: Embed Cache Key in Manifest

The build script should also record the cache key (the hex digest from
`_make_key()`) in the manifest so the runtime loader can detect header
mismatches. Update `build-precompiled.py` to import and call `_make_key`:

```python
from pytanga.codegen._cache import _make_key

# After successful compile:
key = _make_key(dim, sig, dtype)
manifest["algebras"][mod_name] = {
    "dim": dim,
    "sig": sig,
    "dtype": dtype,
    "key": key,
}
```

This way the precompiled `.so` knows exactly which header snapshot it was
built against, and the runtime loader can skip it if the source has changed.

### Step 6: Update Documentation

**File:** `README.md` — Update the "Extras" section to mention that
`[compile]` is only needed when precompiled wheels aren't available.

**File:** `docs/py/env/installation.md` — Document the two installation paths:

```markdown
### Pre-Compiled Wheels (recommended for Linux x86_64)

If a pre-compiled wheel exists for your platform, simply:

```bash
pip install pytanga
```

No C++ compiler or build tools needed. pytanga ships precompiled bindings
for the four most common algebras (E3, P3, N3, PGA3).

### Source Compilation (all platforms)

If no pre-compiled wheel is available for your platform, or if you need
an algebra not covered by the precompiled set, add the `compile` extra:

```bash
pip install pytanga[compile]
```

This pulls in cmake, ninja, and pybind11 for on-the-fly compilation.
```

**File:** `tools/build-precompiled.py` — Add a docstring explaining usage:
```
Usage:
  uv run python tools/build-precompiled.py
  uv build --wheel
```

### Step 7: Manual Build Workflow

For each target platform, run:

```bash
# 1. Ensure pytanga[compile] is installed
uv sync --group dev

# 2. Precompile the common algebras
uv run python tools/build-precompiled.py

# 3. Build the platform wheel
uv build --wheel

# 4. Test: install the wheel WITHOUT [compile] extras
uv run pip install dist/pytanga-*.whl
uv run python -c "
import pytanga
alg = pytanga.Algebra(3, 0)  # E3 — should load from precompiled, no compile
print('E3 module:', alg._module)
"
```

---

## Implementation Order

| Step | File(s) | Description | Effort |
|------|---------|-------------|--------|
| 1 | `tools/build-precompiled.py` (new) | Script to compile and harvest .so files | 30 min |
| 2 | `pyproject.toml` | Add force-include for `precompiled/` | 1 min |
| 3 | `tools/clean-precompiled.py` (new) | Script to remove precompiled artifacts | 5 min |
| 4 | `.gitignore` | Ignore `precompiled/` directory | 1 min |
| 5 | `py/pytanga/codegen/_cache.py` | Add `_load_precompiled()` and integration | 30 min |
| 6 | `tools/build-precompiled.py` | Embed cache key in manifest | 5 min |
| 7 | `README.md`, `docs/py/env/installation.md` | Document precompiled vs source install | 20 min |
| 8 | `tools/upload-pypi.py` (new) | Scripted upload with pre-flight checks | 15 min |
| 9 | — | Manual build & test on Linux, verify wheel tags | 20 min |

**Total: ~2.5 hours.**

---

## Future: CI Pipeline

Once manual builds are proven working:

- GitHub Actions matrix: `ubuntu-latest`, `macos-14` (ARM), `macos-13` (x86_64)
- Each job: install `pytanga[compile]` → run `build-precompiled.py` → build wheel → upload artifact
- Release workflow: attach platform wheels to GitHub Release, optionally push to PyPI via `twine`

---

## What Does NOT Change

| Concern | Status |
|---------|--------|
| `[compile]` extra | Still exists — fallback for unsupported platforms/algebras |
| On-the-fly JIT compilation | Unchanged — still works when precompiled is missing/incompatible |
| `_build.py` | Unchanged — compilation pipeline is untouched |
| `_generator.py` / `_template.cpp` | Unchanged |
| Cache system (`~/.cache/pytanga/`) | Unchanged — precompiled .so is copied into it, not loaded directly |
| Pure `py3-none-any` wheel | Still built when `precompiled/` dir is absent |
| sdist | Unchanged — no `.so` files in source distribution |

---

## Publishing to PyPI

### Manual Upload with `twine`

`twine` is the standard tool for uploading wheels to PyPI. Install it once:

```bash
uv add --group dev twine
```

#### Uploading a Pure Python Wheel

```bash
# 1. Ensure no precompiled artifacts are present
uv run python tools/clean-precompiled.py

# 2. Build the pure wheel
uv build --wheel

# 3. Upload to PyPI
uv run twine upload dist/pytanga-*-py3-none-any.whl
```

#### Uploading Platform-Specific Wheels

Build and upload each platform wheel separately. Example for Linux x86_64:

```bash
# 1. Precompile the common algebras
uv run python tools/build-precompiled.py

# 2. Build the platform wheel (hatchling auto-detects .so and sets tag)
uv build --wheel

# 3. Verify the wheel tag is platform-specific (not py3-none-any)
uv run python -c "
import zipfile
z = zipfile.ZipFile('dist/pytanga-*.whl')
print('Wheel tag is platform-specific (contains .so)')
for n in z.namelist():
    if n.endswith('.so'): print(' ', n)
"

# 4. Upload
uv run twine upload dist/pytanga-*.whl
```

#### Alternative: Scripted Upload (`tools/upload-pypi.py`)

A wrapper script that prompts for confirmation before uploading:

```python
#!/usr/bin/env python3
"""Upload pytanga wheels to PyPI via twine.

Detects whether the wheel in dist/ is a pure wheel or contains precompiled
.so files, prints a summary, and prompts for confirmation before uploading.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"


def main() -> int:
    wheels = sorted(DIST_DIR.glob("pytanga-*.whl"))
    if not wheels:
        print("No wheels found in dist/. Run 'uv build --wheel' first.")
        return 1

    # Take the most recent wheel
    wheel = wheels[-1]
    print(f"Wheel: {wheel.name}")

    # Check for precompiled .so files
    import zipfile
    has_precompiled = False
    with zipfile.ZipFile(wheel) as z:
        for name in z.namelist():
            if name.startswith("pytanga/precompiled/") and name.endswith(".so"):
                has_precompiled = True
                print(f"  precompiled: {name}")

    if has_precompiled:
        print("\nThis is a PLATFORM-SPECIFIC wheel with precompiled binaries.")
    else:
        print("\nThis is a PURE Python wheel (py3-none-any).")

    response = input("\nUpload to PyPI? [y/N]: ").strip().lower()
    if response != "y":
        print("Aborted.")
        return 0

    subprocess.run(
        ["uv", "run", "twine", "upload", str(wheel)],
        check=True,
    )
    print("Upload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### PyPI Configuration

Set up PyPI credentials once:

```bash
# Install twine (done once)
uv add --group dev twine

# Set up PyPI token (stored in ~/.pypirc)
uv run twine check dist/*.whl
```

For CI, use a project-scoped PyPI API token stored as a GitHub Secret
(`PYPI_TOKEN`). The GitHub Actions workflow then uses:

```yaml
- name: Upload to PyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
  run: uv run twine upload dist/*.whl
```

### TODO — Wheel Tag Automation

hatchling should set the correct wheel tag automatically:
- If `precompiled/` contains `.so`/`.dylib`/`.pyd` files → platform-specific tag
  (e.g. `cp312-manylinux_2_35_x86_64`)
- If `precompiled/` is empty or absent → `py3-none-any`

This behavior should be verified during Step 7 (manual build & test). If
hatchling does not auto-detect the platform tag, a `[tool.hatch.build.targets.wheel]`
directive may be needed — this will be investigated during implementation.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Precompiled .so incompatible with user's Python ABI | Medium | Manifest records ABI; loader checks before loading |
| Precompiled .so built against different headers than wheel ships | Medium | Cache key in manifest; loader compares and skips if mismatch |
| .so compiled with different glibc than user's system | Low–Medium | Build on oldest supported distro (e.g. manylinux container); pip wheels already solve this |
| Precompiled wheel is picked up on wrong platform | Very low | pip's wheel tag matching is robust (`cp312-manylinux_x86_64`) |
| `_ga_src/` changes between precompile and wheel build | Low (same session) | Build script bundles both in one session; no gap |
| Pure wheel accidentally includes precompiled .so | Low | `precompiled/` is a build artifact; `.gitignore` + manual build discipline |
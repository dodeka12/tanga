# Precompiled Wheels

pytanga compiles C++ binding modules on demand via JIT compilation. For
users without a C++ compiler, precompiled `.so` files can be bundled into
platform-specific wheels. This document covers the tooling and workflows
for building, cleaning, and uploading precompiled wheels.

## Tools

| Script | Purpose |
|--------|---------|
| `tools/build-precompiled.py` | Compile the five common algebras and harvest `.so` files into `precompiled/` |
| `tools/clean-precompiled.py` | Remove precompiled artifacts to restore a pure Python wheel build |
| `tools/fix-wheel-tag.py` | Rewrite the wheel filename and metadata with the correct platform tag |
| `tools/upload-pypi.py` | Inspect a wheel and upload it to PyPI via twine |

All scripts are run from the repo root with `uv run`.

---

## Workflow: Build a Precompiled Wheel

Use this when you want to ship a wheel that works without a C++ compiler.

```bash
# 1. Ensure dev dependencies are installed (includes [compile] extras)
uv sync --group dev

# 2. Compile and bundle the five common algebras
uv run python tools/build-precompiled.py

# 3. Build the wheel with correct platform tag (one-step via helper script)
# Linux/macOS:
uv run bash tools/build-precompiled-wheel.sh
# Windows:
uv run powershell tools/build-precompiled-wheel.ps1

# 4. Verify
uv run python tools/upload-pypi.py --check
```

**Output:** A platform-specific wheel (e.g. `cp312-cp312-manylinux_2_35_x86_64`)
with precompiled `.so` files for: E3, P3/PGA3, N3 (float64), E3 modular (int64),
and G(10,0) sparse (int64).

The helper scripts `tools/build-precompiled-wheel.sh` (Linux/macOS) and
`tools/build-precompiled-wheel.ps1` (Windows) build to a temp directory,
fix the platform tag via `fix-wheel-tag.py`, move the result to `dist/`,
and clean up — all in one step.

### About the Wheel Tag

hatchling produces `py3-none-any` because the `.so` files in `precompiled/`
are not recognized as Python extension modules. `build-precompiled-wheel.sh`
runs `fix-wheel-tag.py` automatically after the build.

For official manylinux compliance, use `auditwheel` in a manylinux Docker
container instead. The fix-wheel-tag script is intended for local and
ad-hoc builds.

### What `build-precompiled.py` Does

1. Calls `pytanga.codegen._cache.get_or_build()` for each of the five algebras.
   This triggers the same JIT compilation pipeline that users would normally
   pay on first import — but once, at build time.
2. Walks the cache directory (`~/.cache/pytanga/`) to find the compiled `.so`
   for each module name.
3. Copies each `.so` into `precompiled/` at the repo root.
4. Writes `precompiled/manifest.json` recording platform, ABI, compiler info,
   and a **cache key** (SHA-256 hash of all C++ headers and codegen Python
   files) for each algebra.

The `precompiled/` directory is included in the wheel via hatchling's
`[tool.hatch.build.targets.wheel.force-include]` in `pyproject.toml`.

---

## Workflow: Build a Pure Python Wheel

Use this when you want to build a `py3-none-any` wheel with no precompiled
binaries (the default, portable wheel).

```bash
# 1. Remove precompiled artifacts (if any)
uv run python tools/clean-precompiled.py

# 2. Build the wheel
uv build --wheel
```

**Output:** A `py3-none-any` wheel containing only Python code and C++
headers (`_ga_src/`). Users need the `[compile]` extra to use this wheel.

`clean-precompiled.py` removes everything from `precompiled/` except
`.gitkeep`, so the directory stays tracked by git but the next wheel
build produces a pure wheel.

---

## Workflow: Upload to PyPI

```bash
# 1. Build and tag the wheel (precompiled or pure, see above)
uv build --wheel
uv run python tools/fix-wheel-tag.py      # only needed for precompiled wheels

# 2. Inspect the wheel
uv run python tools/upload-pypi.py --check

# 3. Upload (interactive — prompts for confirmation)
uv run python tools/upload-pypi.py

# Or upload to Test PyPI first:
uv run python tools/upload-pypi.py --repo testpypi
```

`upload-pypi.py` inspects the newest wheel in `dist/`, reports whether it
is a pure wheel or contains precompiled `.so` files, and prompts for
confirmation before running `twine upload`.

**Prerequisites:** `twine` must be installed and PyPI credentials configured.
Add twine via `uv add --group dev twine`, then set up a PyPI API token in
`~/.pypirc` or via `TWINE_USERNAME` / `TWINE_PASSWORD` environment variables.

---

## Runtime Behavior

When a user imports an algebra (e.g. `pytanga.Algebra(3, 0)`), the cache
layer runs this priority chain:

1. **Cache hit** — `.so` already exists in `~/.cache/pytanga/<key>/` → load instantly.
2. **Precompiled check** — Look for a matching entry in `pytanga/precompiled/manifest.json`.
   If found, compare the cache key. If the key matches (C++ headers haven't
   changed since the wheel was built), copy the `.so` into the cache and load
   it. If the key doesn't match, skip the precompiled binary.
3. **JIT compilation** — Generate, compile, and load the binding. This requires
   the `[compile]` extras (cmake, ninja, pybind11) and a C++ compiler.

The key-based check means a precompiled binary is automatically invalidated
if the C++ headers change between releases. Users with a compiler experience
self-healing behavior: the outdated precompiled binary is skipped, and JIT
compilation produces a correct binding.

---

## Directory Layout

```
precompiled/                          # ← at repo root, git-ignored except .gitkeep
├── .gitkeep                          # keep directory tracked when empty
├── manifest.json                     # metadata: platform, ABI, keys, algebra list
├── binding_dim3_sig0_float64.cpython-312-x86_64-linux-gnu.so
├── binding_dim4_sig8_float64.cpython-312-x86_64-linux-gnu.so
├── binding_dim5_sig16_float64.cpython-312-x86_64-linux-gnu.so
├── binding_dim3_sig0_int64.cpython-312-x86_64-linux-gnu.so
└── binding_dim10_sig0_int64.cpython-312-x86_64-linux-gnu.so
```

The `.so` filenames include Python ABI tags (e.g. `.cpython-312-x86_64-linux-gnu.so`),
which pip uses to determine platform compatibility. The runtime loader matches
files by module name prefix, ignoring the ABI suffix.

The `pyproject.toml` force-include maps `precompiled/` into the wheel at
`pytanga/precompiled/`. In a dev checkout, the loader also checks the
repo-root `precompiled/` directory (for testing before building the wheel).

---

## Manifest Format

```json
{
  "version": 1,
  "platform": "Linux-7.0.0-28-generic-x86_64-with-glibc2.39",
  "python_abi": "cp312",
  "compiler": "g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0",
  "algebras": {
    "binding_dim3_sig0_float64": {
      "dim": 3,
      "sig": 0,
      "dtype": "float64",
      "key": "1cbb8d45fab331a3cb84bf02ae01424b1494608970cb58c4577890d298615f9c"
    }
  }
}
```

The `key` field is the SHA-256 digest from `pytanga.codegen._cache._make_key()`.
It covers the algebra identity (dim, sig, dtype), all C++ headers under
`TANGA_SOURCE`, the binding template `_template.cpp`, and all Python files
in the `codegen/` package.

## Related Files

| File | Role |
|------|------|
| `py/pytanga/codegen/_cache.py` | `_load_precompiled()` runtime loader |
| `py/pytanga/codegen/_build.py` | JIT compilation pipeline (`build_and_load()`) |
| `pyproject.toml` | `force-include` for `precompiled/` and `_ga_src/` |
| `.gitignore` | Ignores `precompiled/*` except `.gitkeep` |
| `dev/todos/precompiled-wheels.md` | Full implementation plan |
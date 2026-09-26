# Phase 3 — Build + precompile + runtime dispatch

## Goal

Register `binding_piz` in the cache/precompiled layer and make `read_exr` use
it automatically, falling back to the numpy path when no binary is available.

## Files

- Edit: `py/pytanga/codegen/_cache.py` (or a small `_piz_cache.py` next to it)
- Edit: `tools/build-precompiled.py`
- Edit: `py/pytanga/viz/_image_io.py`
- Edit: `py/pytanga/viz/image.py` (re-export a force-Python flag helper, optional)

## Steps

- [x] **3.1 — `get_or_build_piz()` loader**
  - Add a fixed-key cache path for `binding_piz`: key = SHA-256 of
    `binding_piz.cpp` + `codegen/CMakeLists.txt` (+ `_build.py`-relevant bits),
    mirroring `_cache._make_key` but without the (dim, sig, dtype) identity.
  - Priority chain: cache hit → precompiled (`precompiled/` manifest `"piz"`
    entry) → JIT via `_build.build_binding(..., module_name="binding_piz")`.
    Load with `_cache._load`.  Return `None` (or raise a sentinel the caller
    catches) when no compiler/binary is available.

- [x] **3.2 — Precompiled-wheel integration**
  - In `tools/build-precompiled.py`, compile `binding_piz` via the loader and
    copy its `.so`/`.pyd` into `precompiled/`; add a `"piz": {"key": …}` entry
    to `manifest.json` (alongside `"algebras"`).
  - Update `docs/dev/workflows/precompiled-wheels.md` later (phase 4).

- [x] **3.3 — Runtime dispatch in `_piz_uncompress`**
  - `_piz_uncompress`: raw fallback first; then try
    `binding_piz.piz_decode(chunk, width, n_lines, sizes)`; on `ImportError`
    or a load/build failure, fall back to the numpy decode.
  - Honor `PYTANGA_FORCE_PURE_PYTHON=1` to skip the C++ path (for tests/perf).
  - Cache the loaded module / "unavailable" result on the module so the lookup
    happens once, not per chunk.

## Results

- `read_exr(docklands_02_4k.exr)` (4096×2048 RGBA float, PIZ, 64 chunks):
  **~1.5 s end-to-end** via `binding_piz` (vs ~50 s numpy fallback, >30 min
  original).  `PYTANGA_FORCE_PURE_PYTHON=1` takes the numpy path unchanged.
- `pytest` (both paths), `ruff check py/`, and `ty check` all pass.

## Validation

```
uv run pytest py/tests/viz/test_image_io.py -q   # numpy path still green
PYTANGA_FORCE_PURE_PYTHON=1 uv run pytest py/tests/viz/test_image_io.py -q
uv run python tools/build-precompiled.py          # needs [compile] extras + g++
```

## Notes

- The C++ path is best-effort: any failure (missing `pybind11`/compiler, load
  error, decode error) must degrade silently to the numpy path without
  changing `read_exr`'s public behavior.
- `binding_piz` is a **fixed** binding (no per-parameter identity), so it does
  not use `_generator.module_name(dim, sig, dtype)` — it always compiles to the
  literal module name `binding_piz`.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

# EXR PIZ performance: numpy fallback + C++ binding — Overview

**Created:** 2026-09-26 | **Status:** Done | **Branch:** `fix/image-display`

## Goal

Make `read_exr` load large PIZ-compressed EXRs in seconds instead of minutes.
The pure-Python PIZ decoder (Huffman + wavelet + LUT in `_image_io.py`) takes
>30 s per 32-scanline chunk for a 4096×2048 file (~64 chunks ≈ >30 min).  Fix
it two ways, in this order:

1. **Pure-Python numpy fallback** — vectorize the hot paths so a
   dependency-free install still loads a 4K EXR in roughly 1–2 min.
2. **C++ fast path** — port the PIZ decode to a small pybind11 `binding_piz`
   extension, compiled/precompiled via the existing `codegen` machinery (like
   the algebra bindings), used automatically when available.

## Architecture (short)

- `py/pytanga/viz/_image_io.py` — `read_exr` / `_piz_uncompress` stay the
  public surface.  `_piz_uncompress` keeps its contract (returns interleaved
  little-endian `uint16` bytes) and dispatches internally: raw-fallback → C++
  `binding_piz.piz_decode` → numpy fallback.
- `py/pytanga/codegen/` — reuse the existing pybind11 JIT build
  (`_build.build_binding`, `CMakeLists.txt`) and cache/precompiled layer
  (`_cache`), extended with a **single fixed** `binding_piz` (not the
  per-(dim,sig,dtype) algebra binding).
- `tools/build-precompiled.py` + `precompiled/` — bundle the `binding_piz`
  extension for users without a compiler (same wheel pipeline as the algebra).

## Fixed contract (up front)

- **C++ binding** — `binding_piz.piz_decode(chunk: bytes, width: int,
  n_lines: int, sizes: Sequence[int]) -> bytes`.  Returns interleaved
  little-endian `uint16` pixel bytes (`n_lines * width * sum(sizes)` shorts).
  `sizes` = per-channel short counts (1 = HALF, 2 = FLOAT/UINT), in channel
  order.
- **numpy fallback** — the same interleaved-bytes result for the same inputs,
  so `read_exr` output is identical either way.
- **Dispatch** — `_piz_uncompress` first handles the raw (uncompressed)
  fallback, then tries the C++ binding, then the numpy fallback.  An env var
  `PYTANGA_FORCE_PURE_PYTHON=1` forces the Python path (tests/perf).
- **Scope** — only the PIZ decode moves to C++; header/container parsing, the
  RLE/ZIPS/ZIP/NONE codecs, channel selection, and `_unpack_exr_raw` stay in
  Python/numpy.  No numba/Cython, no `OpenEXR` PyPI dependency.

## Decisions (confirmed)

- C++ source is a single self-contained `py/pytanga/codegen/binding_piz.cpp`
  (PIZ decode + `PYBIND11_MODULE`), adapted from the BSD-3-Clause
  tinyexr/OpenEXR reference (`DecompressPiz` / `hufUncompress` / `wav2Decode`)
  with an attribution comment.  It does not depend on Tan.* headers.
- `binding_piz` is compiled with the existing `codegen/CMakeLists.txt` (which
  also compiles the three Tan.* impl files — harmless) and loaded via
  `_cache._load`.
- The C++ path is **optional**: without `[compile]` extras + a C++ compiler and
  without a precompiled wheel, `read_exr` transparently uses the numpy fallback.
- Precompiled-wheel manifest gains a `"piz"` entry (a single fixed key = hash
  of `binding_piz.cpp` + `codegen/CMakeLists.txt`), alongside `"algebras"`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-numpy-fallback.md](./01-python-numpy-fallback.md) | Vectorize LUT / Huffman runs / wavelet so the pure-Python path is usable ✅ |
| 2 | [02-cpp-piz-decode.md](./02-cpp-piz-decode.md) | C++ PIZ decode + pybind11 `binding_piz` module ✅ |
| 3 | [03-build-precompile-runtime.md](./03-build-precompile-runtime.md) | Cache/precompile integration + `read_exr` dispatch with fallback ✅ |
| 4 | [04-tests-docs-changelog.md](./04-tests-docs-changelog.md) | Round-trip/perf tests, dev + user docs, changelog ✅ |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_image_io.py -q`
- Full: `uv run pytest -q`, `uv run ruff check py/`, `uv run ty check`
- Perf: `uv run python -c "… read_exr('~/Bilder/docklands_02_4k.exr', on_progress=print) …"` (manual)
- C++ build/precompile: `uv run python tools/build-precompiled.py` (needs `[compile]` extras + a C++ compiler)
- Docs: `uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Non-goals

- Not porting the whole EXR reader to C++ (only the PIZ decode hot path).
- No numba / Cython / `OpenEXR` package dependency.
- Not changing the `read_exr`/`read_hdr` public API or return shape.
- No cross-platform wheel CI in this plan (local `tools/build-precompiled.py` only).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

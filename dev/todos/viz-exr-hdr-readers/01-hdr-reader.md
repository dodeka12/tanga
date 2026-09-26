# Phase 1 — Radiance RGBE reader

## Goal

Implement `read_hdr` in `_image_io.py`: parse a Radiance `.hdr`/`.pic` file and
return a `float32` `(H, W, 3)` array, with no third-party dependencies.

## Files

- New: `py/pytanga/viz/_image_io.py`
- New: `py/tests/viz/test_image_io.py`
- New: `py/tests/viz/data/*.hdr` (fixtures)

## Steps

- [x] **1.1 — Header + resolution line**
  - Detect `#?RADIANCE`/`#?RGBE`; read lines to the blank line.
  - Parse the resolution line (`-Y H +X W` and the sign/order variants):
    extract width/height and row/column flip/rotation flags; reject unknown
    orientations with a clear error.
- [x] **1.2 — Pixel decode**
  - Implement uncompressed (flat RGBE) + new (adaptive) RLE; a non-new-RLE
    scanline header is read as flat (matching the reference reader — legacy
    old RLE is not decoded).
  - RGBE→float per pixel: `v = (m + 0.5) / 256.0 * 2.0 ** (e - 128)`, with
    `e == 0 → 0.0`; assemble `float32 (H, W, 3)` honoring the orientation flags.
- [x] **1.3 — Public entry + re-export**
  - `read_hdr(source)` accepting `str | Path | bytes`; raise `ValueError` on
    malformed input.
  - Re-export `read_hdr` from `pytanga.viz.image` (`__all__`).
- [x] **1.4 — Fixtures + tests**
  - Hand-crafted inline fixtures (flat + new RLE, tiny 2×2 images with known
    RGB values, including `> 1` and `0` exponent cases, plus `+Y`/`-X`
    orientation).
  - Test dims, dtype, orientation, pixel values, source types, and errors.

## Validation

```
uv run pytest py/tests/viz/test_image_io.py -q
```

## Notes

- RGBE uses a shared exponent, so a row's values share one byte; the decode is
  branch-light and vectorisable with numpy for the uncompressed path.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

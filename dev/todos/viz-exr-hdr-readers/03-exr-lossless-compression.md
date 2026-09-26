# Phase 3 — EXR RLE + ZIPS + ZIP

## Goal

Add the `RLE`, `ZIPS`, and `ZIP` decompressors to `read_exr`.

## Files

- Edit: `py/pytanga/viz/_image_io.py`
- Edit: `py/tests/viz/test_image_io.py`
- New: `py/tests/viz/data/*.exr` (fixtures)

## Steps

- [x] **3.1 — RLE (codec 1, 1 line/chunk)**
  - Decode the OpenEXR RLE scheme (signed count byte: `>= 0` → `count+1`
    literal bytes; `< 0` → next byte repeated `-count` times) into the raw
    scanline buffer of `width * bytes_per_pixel`.
- [x] **3.2 — ZIPS (codec 2, 1 line/chunk)**
  - Read the 2-byte little-endian size prefix, `zlib.decompress`, and validate
    the size.
- [x] **3.3 — ZIP (codec 3, 16 lines/chunk)**
  - Read the 2-byte size prefix, `zlib.decompress`, then undo OpenEXR's
    per-pixel byte **reorder** (swap the two byte groups within each pixel,
    matching the reference implementation) before reshaping to scanlines.
- [x] **3.4 — Fixtures + tests**
  - Inline fixture generator encodes `RLE`/`ZIPS`/`ZIP` files; round-trip tests
    assert decode equals the known pixels, plus a direct reorder test that pins
    the half-swap against a literal byte sequence.

## Validation

```
uv run pytest py/tests/viz/test_image_io.py -q
```

## Notes

- The ZIP/ZIPS size prefix is the uncompressed byte count; use it to detect
  truncation/corruption.
- The reorder is the subtle part; it must match `ImfZipCompressor::reorder`
  exactly, so pin it with a reference fixture rather than a round-trip only.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

# Phase 4 — EXR PIZ

## Goal

Add the `PIZ` (lossless wavelet) decompressor to `read_exr`, the common HDRI
EXR codec and older Blender default.

## Files

- Edit: `py/pytanga/viz/_image_io.py`
- Edit: `py/tests/viz/test_image_io.py`
- New: `py/tests/viz/data/*_piz.exr` (fixture)

## Steps

- [x] **4.1 — Huffman decode**
  - Port the PIZ Huffman table + bit-reader; unpack each 16-bit coefficient
    using the reference `hufUncompress` scheme (including the run-length
    short-encoding).
- [x] **4.2 — Inverse wavelet**
  - Port the inverse Haar-like wavelet (`wav2Decode`) that reconstructs the
    per-channel 16-bit values from the coefficients.
- [x] **4.3 — Range expansion + byte reconstruction**
  - Undo the PIZ range compression (bitmap + reverse LUT) and reassemble the
    channel shorts into an interleaved scanline buffer, including the raw
    fallback (channel-planar-per-scanline) that OpenEXR stores when PIZ
    wouldn't shrink the data.
- [x] **4.4 — Fixture + test**
  - Generate a small `PIZ` reference file (dev-time, OpenEXR library in a
    throwaway venv) and commit it; assert known pixel values.
  - Add a `NOTICE`/attribution note for the ported algorithm (BSD-3-Clause
    `tinyexr`/OpenEXR heritage) if code is closely derived.

## Validation

```
uv run pytest py/tests/viz/test_image_io.py -q
```

## Notes

- PIZ is the most intricate codec here (~250 lines); implement it against the
  OpenEXR reference and validate only against an independent fixture — never
  against a self-written encoder.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

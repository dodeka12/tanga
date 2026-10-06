# Phase 2 — EXR container + NONE + channel/type decode

## Goal

Parse the OpenEXR container (magic, version, header, offset table, scanline
chunks) and decode uncompressed (`NONE`) files, returning a `float32`
`(H, W, C)` array.

## Files

- Edit: `py/pytanga/viz/_image_io.py`
- Edit: `py/tests/viz/test_image_io.py`
- New: `py/tests/viz/data/*.exr` (fixtures)

## Steps

- [x] **2.1 — Magic + version**
  - Read magic `20000630` (`76 2f 31 01`); read the 2-byte version field and
    reject tiled/deep/multi-part (`0x200`/`0x800`/`0x1000`).
- [x] **2.2 — Header**
  - Parse the attribute list (`name\0`, `type\0`, `int32 size`, value; ended by
    an empty name).  Extract `channels` (chlist), `compression` (int32),
    `dataWindow` (box2i), `lineOrder` (int32); ignore other attributes.
  - Decode chlist entries (name, `int32` pixel type, `u8` pLinear, 3 reserved
    bytes, `int32` xSampling, `int32` ySampling); require sampling `1`.
- [x] **2.3 — Offset table + chunks**
  - Read one `int64` per chunk; for each chunk read `int32 y`, `int32 size`,
    and `size` data bytes; place rows per `lineOrder` (increasing/decreasing).
- [x] **2.4 — NONE decode + channel types**
  - `UINT`→`<u4`, `HALF`→`<f2` (then `astype(float32)`), `FLOAT`→`<f4`.
  - Interleave channels in chlist order; assemble `float32 (H, W, C)` where
    `C` is `len(channels)` capped at 4 (keep R/G/B(/A); for arbitrary channels
    keep the first up-to-4).
- [x] **2.5 — Fixtures + tests**
  - Hand-crafted inline `NONE` fixtures (half/float/uint channel types) with
    known pixel values; error cases for bad magic, tiled, and unsupported
    compression.

## Validation

```
uv run pytest py/tests/viz/test_image_io.py -q
```

## Notes

- `bytes` order is little-endian throughout.
- `displayWindow` is intentionally ignored (no crop/offset applied); the
  returned array is the `dataWindow` extent.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

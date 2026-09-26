# Phase 1 — Backend `zlib` tile format

## Goal

Add a lossless **`zlib`** tile format to `ImagePyramid` that compresses the raw
source-dtype tile bytes, reusing the frame codec's encoder.

## Files

- Edit: `py/pytanga/viz/_image_pyramid.py`
- Edit: `py/tests/viz/test_image_pyramid.py`

## Steps

- [x] **1.1 — `zlib` tile format**
  - Add `"zlib": "application/octet-stream"` to `FORMAT_CONTENT_TYPE`.
  - Import `encode_zlib_raw` from `._image_wire` and, in `ImagePyramid._encode`,
    handle `format == "zlib"` by returning `encode_zlib_raw(tile)`.

- [x] **1.2 — backend tests**
  - Add `test_zlib_tile_round_trips_losslessly`: for a `float32` and a `uint16`
    pyramid, `zlib.decompress(get_tile(0, x, y, "zlib"))` equals
    `get_tile(0, x, y, "raw")` for the same tile (edge tile included).
  - Confirm the existing `raw` behavior is unchanged.

## Validation

```
uv run pytest py/tests/viz/test_image_pyramid.py -q
uv run ruff check py/pytanga/viz/_image_pyramid.py py/tests/viz/test_image_pyramid.py
uv run ty check
```

## Notes

- `_image_pyramid.py` stays data-only: `zlib` is stdlib and `_image_wire` is a
  sibling pure-data module (no server imports, no circular import — `_image_wire`
  only imports `image`).
- `Content-Type` is `application/octet-stream` (compressed bytes), same as `raw`.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

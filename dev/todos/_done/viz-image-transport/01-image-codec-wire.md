# Phase 1 — Python codec layer + wire v2

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a codec to the image wire format (v2) and a lazy-Pillow encoder so the
backend can send compressed frames.  This phase is pure Python (no JS) and is
validated by unit tests.

## Files

- Edit: `py/pytanga/viz/_image_wire.py`
- Edit: `py/pytanga/viz/image.py`
- Edit: `pyproject.toml`
- New: `py/tests/viz/test_image_codec.py` (or extend existing wire tests)

## Steps

- [x] **1.1 — `ImageCodec` enum + `codec`/`jpeg_quality` on `ImageData`**
  - In `image.py`, add an `ImageCodec` enum (`RAW=0`, `JPEG=1`, `ZLIB_RAW=2`) and
    optional `codec: str | None = None` / `jpeg_quality: int | None = None`
    fields on `ImageData` (ignored for `url` images).
  - Add `ImageData.supports_jpeg` (`uint8` and 1 or 3 channels).

- [x] **1.2 — encode/decode helpers (`_image_wire.py`)**
  - Add `encode_jpeg(arr, quality=85) -> bytes` (lazy `PIL.Image.fromarray`;
    raise a clear `ImportError` if Pillow is missing and JPEG is requested).
  - Add `encode_zlib_raw(arr) -> bytes` using stdlib `zlib.compress`.
  - Bump `_VERSION = 2`; change `_HEADER` to `struct.Struct("<BBBBIIBBQ")` with
    the `codec` byte at offset 3 (see README contract).
  - `encode_image_frame(image_id, data, *, codec="auto", jpeg_quality=85)`:
    auto-select JPEG (uint8 1/3ch), else zlib-raw; `codec="raw"` keeps today's
    exact output.  Reject unknown codecs.
  - `decode_image_frame` accepts v1 (codec implied 0) and v2; returns a new
    `codec` key (`"raw"`/`"jpeg"`/`"zlib_raw"`) and the payload bytes.

- [x] **1.3 — propagate codec from callers**
  - Thread `ImageData.codec`/`jpeg_quality` through the two encode call sites:
    `_image_view._sync_image` and `_layout._collect_background_frames` /
    `_layout.push_background_image`.  Default stays `"auto"`.

- [x] **1.4 — optional runtime extra**
  - Add `[project.optional-dependencies] images = ["pillow>=10"]` to
    `pyproject.toml` (Pillow stays out of the core runtime deps).

- [x] **1.5 — unit tests**
  - Round-trip each codec (raw/jpeg/zlib_raw) for `uint8`/`uint16`/`float32`,
    verifying `decode(encode(...))` recovers dims/dtype/id and (for raw/zlib)
    exact pixel equality.
  - Assert v1 frames still decode; assert auto-selection rules; assert JPEG
    fails with a clear error when Pillow is unavailable.

## Validation

```powershell
uv run pytest py/tests/viz -q
uv run ruff check py/pytanga/viz/_image_wire.py py/pytanga/viz/image.py py/tests/viz
```

## Notes

- `zlib.compress(arr.tobytes())` is the lossless path; it needs no Pillow, so
  float/16-bit scientific data remains lossless out of the box.
- Keep `to_base64()` unchanged in this phase (it is the export path; Phase 3
  adds JPEG there).

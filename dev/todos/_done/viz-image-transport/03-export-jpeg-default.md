# Phase 3 — JPEG-by-default in exported HTML

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Emit eligible images (`uint8`, 1 or 3 channels) as `data:image/jpeg;base64,…`
data URLs in the export asset store instead of raw base64, reusing the
frontend's existing `url` texture path.  Ineligible images keep raw base64.

## Files

- Edit: `py/pytanga/viz/image.py` (`to_jpeg_data_url` helper)
- Edit: `py/pytanga/viz/export/_animation_recording.py` (`_image_asset`)
- Edit: `py/tests/viz/test_image_canvas_export.py` (and/or `test_image.py`)

## Steps

- [x] **3.1 — `ImageData.to_jpeg_data_url(quality=85)`**
  - Lazy-Pillow encode to JPEG bytes, return `data:image/jpeg;base64,…`.
  - Raise a clear `ImportError` for unsupported dtypes/channels or missing
    Pillow (same wording family as `pil_to_numpy`).

- [x] **3.2 — asset store emits JPEG data URLs by default**
  - In `_animation_recording._image_asset`: when `img.supports_jpeg`, emit
    `{"kind": "image", "source": "url", "url": <jpeg data url>, "width":…,
    "height":…, "channels":…, "dtype":…}`; otherwise keep
    `{"source": "data", "data": <raw base64>}`.
  - This is the single choke point the animated export uses.

- [x] **3.3 — tests**
  - Extend `TestAssetStore`: a uint8 RGB image now yields `source == "url"` and
    a `url` starting with `data:image/jpeg;base64,`; a `uint16`/`float32`/4-ch
    image still yields `source == "data"` + raw base64.

## Validation

```powershell
uv run pytest py/tests/viz/test_image_canvas_export.py py/tests/viz/test_image.py -q
uv run ruff check py/pytanga/viz/image.py py/pytanga/viz/export/_animation_recording.py
```

## Notes

- The frontend needs no change here: `renderers/image.js` and
  `image-background.js` already load `source === "url"` images via
  `THREE.TextureLoader`/`Image`, which decodes data URLs natively.
- Confirm the export viewer's animated bootstrap hydrates the asset's `url`
  into the image meta (it already does for URL images); no new decode code.
- Static (non-animated) snapshot export does **not** currently embed image
  pixel bytes at all — a pre-existing gap, out of scope (see README Non-goals).

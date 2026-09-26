# Phase 2 — Reset image value range on `set_image`

## Goal

Replacing the primary image with a different dtype re-derives `u_mode`,
`u_value_min`, and `u_value_max`, so a `uint16` image loaded after a `uint8`
placeholder no longer keeps `u_value_max = 1.0` and clamps to white.

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/tests/viz/test_image_canvas_integration.py` (or nearest image test)

## Steps

- [x] **2.1 — Overwrite the seeded defaults on `set_image`**
  - Add `ImageView._reset_image_defaults(image)` that **assigns**
    `u_mode = default_mode(image.channels)` and
    `u_value_min`/`u_value_max = default_value_range(image.dtype)`.
  - Call `_reset_image_defaults` from `set_image` (replacing the current
    `_seed_image_defaults` call); keep `_seed_image_defaults` (`setdefault`)
    for `add_image`.
- [x] **2.2 — Test**
  - Add a test asserting that after `set_image(uint8 image)` then
    `set_image(uint16 image)`, `image_view.uniforms` has `u_value_max == 65535`
    (and `u_mode` follows the new channel count).

## Validation

```
uv run pytest py/tests/viz/test_image_canvas_integration.py py/tests/viz/test_image_canvas.py -q
```

## Notes

- `set_image` is "replace the primary image", so re-deriving the natural value
  range is correct; callers that want a custom range call `set_uniform` **after**
  `set_image` (as the existing `raw_image.py` pattern does).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

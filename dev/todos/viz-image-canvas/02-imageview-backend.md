# Phase 2 — `ImageView` backend (plane + textures + shader/uniform state)

## Goal

The low-level backend object that owns the active draw plane, up to 4 images,
the shader source, and the uniform values, and serializes to the canonical
`image` entity dict.  Pure data + validation; no server/rendering.

## Files

- New: `py/pytanga/viz/_image_view.py` (`ImageView` part)
- New: `py/tests/viz/test_image_view.py`
- Edit: `py/pytanga/viz/__init__.py` (re-export `ImageView`)

## Steps

- [x] **2.1 — `ImageView` state**
  - Holds `images: list[ImageData]` (max 4, enforced on `add_image`/`set_image`),
    `shader` (fragment source + optional vertex source), `uniforms: dict[str,
    float|int]`, and `frame: (width, height)`.
  - Methods: `set_image` (replace layer 0), `add_image` (next slot), `set_uniform`,
    `register_uniform(name, default)`, `register_shader(fragment, vertex=None)`.

- [x] **2.2 — standard shader defaults**
  - Seed `uniforms` with `u_brightness=0.0`, `u_contrast=1.0`, `u_midpoint=0.5`,
    and a `u_mode` default derived from channels (1→`0`, 3/4→`1`).
  - Add `u_value_min`/`u_value_max` from `default_value_range`.

- [x] **2.3 — channel-mode + normalization constants**
  - `ImageChannelMode` (`GRAY=0`, `RGB=1`, `MAGNITUDE=2`, `ALPHA=3`) and a
    `default_mode(channels)` helper matching the README contract.

- [x] **2.4 — `_serialize()` → `image` entity dict**
  - Emit exactly the README `Image entity` shape: `{id, layer:"scene",
    kind:"image", frame, images[], shader{}, uniforms{}}`, with per-image
    `source`/`url` fields.

- [x] **2.5 — re-export `ImageView`**
  - Add to `py/pytanga/viz/__init__.py` + `__all__`.

- [x] **2.6 — Unit tests `py/tests/viz/test_image_view.py`**
  - 4-layer cap raises; serialization matches the README contract (spot-check
    JSON); `set_uniform`/`register_uniform`; channel-mode defaults per channel
    count; uniform dict round-trips.

## Validation

`uv run pytest py/tests/viz/test_image_view.py -q && uv run ruff check py/pytanga/viz/_image_view.py py/tests/viz/test_image_view.py`

## Notes

- Keep `ImageView` serializer free of rendering/server imports (mirrors
  `views.py`'s "pure data + validation" contract).
- The `image` entity is a new scene-object kind; the frontend dispatch lands in
  Phase 6 — do not wire it to `factory.js` yet.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.

# Phase 1 — Python: shared shader/uniform model

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Image
> canvas (extension recipe)" and "Camera view (extension recipe)").  This phase
> extends the `CameraView.background_image` contract; the doc update lands in
> Phase 6.

## Goal

Extract the shader/uniform/image state from `ImageView` into a reusable form and
let `CameraView.background_image` carry it, so both the canvas and the background
share one model.  Frontend is unchanged in this phase.

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/pytanga/viz/views/camera_view.py`
- Edit: `py/pytanga/viz/views/_helpers.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_image_view.py`
- Edit: `py/tests/viz/test_image_background.py`

## Steps

- [x] **1.1 — Split `ImageView` serialization into shared state + scene envelope.**
  - Add `ImageView._serialize_state()` returning
    `{"images": [...], "shader": {"fragment", "vertex"}, "uniforms": {...}}`
    (the shared payload, no `id`/`layer`/`kind`/`frame`).
  - Reimplement `_serialize()` (the scene `image` entity) on top of
    `_serialize_state()`, adding the `id`/`layer`/`kind`/`frame` envelope.  No
    behavior change to the existing `image` entity dict.
  - Add accessors used by the background path if missing (the class already has
    `images`, `uniforms`, and `register_shader`/`register_uniform`/`set_uniform`).

- [x] **1.2 — Accept an `ImageView` as `CameraView.background_image`.**
  - In `CameraView.__post_init__`, normalize `background_image`: a bare `ImageData`
    is wrapped into an `ImageView(image.id)` with `set_image(image)` (default
    shader + seeded uniforms); an `ImageView` is kept as-is.
  - Keep the `background_image` attribute readable as the `ImageView`.

- [x] **1.3 — Serialize `shader`/`uniforms` into the background metadata.**
  - In `views/_helpers.py`, extend `_image_meta` (or add a sibling
    `_background_image_meta`) so that, given an `ImageView`, it emits the existing
    `_image_meta` fields for the primary image **plus** `"shader"` and
    `"uniforms"` from `_serialize_state()`.
  - `CameraView.to_dict()` uses this for the `background_image` field.

- [x] **1.4 — Tests.**
  - `test_image_view.py`: `_serialize_state()` returns the shared payload;
    `_serialize()` is unchanged in shape.
  - `test_image_background.py`: `CameraView(background_image=ImageData(...))`
    serializes with seeded `uniforms` (`u_brightness`/`u_contrast`/`u_midpoint`
    + value-range keys) and `shader == {"fragment": None, "vertex": None}`;
    a custom uniform registered on the `ImageView` round-trips.

## Validation

`uv run pytest py/tests/viz/test_image_view.py py/tests/viz/test_image_background.py -q`

## Notes

- Do not change `renderers/image.js` or `image-background.js` here — the frontend
  ignores the new `shader`/`uniforms` keys until Phase 3.
- `ImageData` auto-tiling and the value-range seeding already live in `image.py`
  (`default_mode`/`default_value_range`); reuse them for the background's seeded
  uniforms rather than duplicating.
- Wrapping `background_image` into an `ImageView` requires unwrapping the primary
  image in the existing consumers (`_layout.py::_collect_background_frames` /
  `push_background_image`, `visualizer.py::_register_background_pyramids`); this
  unwrap lands here so the model change stays green.

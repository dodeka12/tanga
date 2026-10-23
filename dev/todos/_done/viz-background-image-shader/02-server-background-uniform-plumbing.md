# Phase 2 — Server: background uniform/shader plumbing

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Image
> background" and "Granular updates").  This phase adds the `view_background_uniforms`
> message and threads `shader`/`uniforms` through the existing background push.

## Goal

Add the server-side granular uniform message and the public `Visualizer` API, and
make image swaps carry the shader/uniform state through the existing
`view_background_image` / `_collect_background_frames` paths.

## Files

- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_image_background.py`
- Edit: `py/tests/viz/test_image_canvas_integration.py`

## Steps

- [x] **2.1 — `LayoutHost.push_background_uniforms(view, patch)`.**
  - Assert `view` is a `SceneView`; send
    `{"type": "view_background_uniforms", "view_id": view.id, "uniforms": dict(patch)}`.
  - Mirror the structure of `push_background_image` (imports, view check).

- [x] **2.2 — Thread `shader`/`uniforms` through background pushes.**
  - In `push_background_image(view, image)`: when `image` is a bare `ImageData`,
    update the existing `view.camera_view.background_image` primary image **without
    resetting** its `uniforms`/`fragment`/`vertex` (preserve brightness/contrast +
    custom shader across an image swap); when `image` is an `ImageView`, replace
    the whole state.
  - Send the background metadata (with `shader`/`uniforms`) from Phase 1's helper.
  - `_collect_background_frames` continues to iterate the primary image for pixel
    frames; the `view_layout`/`camera_view` serialization already carries
    `shader`/`uniforms` via Phase 1.

- [x] **2.3 — Public `Visualizer` API.**
  - Add `register_background_shader(view, fragment, vertex=None)`,
    `register_background_uniform(view, name, default)`, and
    `set_background_uniform(view, name, value)`.
  - `register_*` mutate `view.camera_view.background_image` and (for shader)
    re-push the background so the frontend rebuilds the material with the new
    source; `set_background_uniform` delegates to `push_background_uniforms`.
  - Register tiled pyramids as `set_background_image` already does, if relevant.

- [x] **2.4 — Tests.**
  - `test_image_background.py`: `set_background_uniform` emits exactly one
    `view_background_uniforms` message (no binary frame); `register_background_shader`
    re-pushes `view_background_image` with the new `shader`.
  - `test_image_canvas_integration.py` (if applicable): confirm the canvas
    `image_update` path is unaffected.

## Validation

`uv run pytest py/tests/viz/test_image_background.py py/tests/viz/test_image_canvas_integration.py -q`

## Notes

- The uniform message is view-level (keyed by `view_id`), unlike the canvas's
  `image_update` (keyed by scene-entity `id`).  Do not reuse `image_update` for
  the background.
- `set_background_uniform` must not send pixel bytes; it is the background analog
  of `ImageCanvas.set_uniform`.

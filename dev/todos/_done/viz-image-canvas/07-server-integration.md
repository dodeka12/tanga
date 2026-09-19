# Phase 7 — Server integration + `Visualizer` glue

## Goal

Route the `image` entity and the `image_update` uniform message through the
serializer/server, send image bytes once per `set_image`, and let
`Visualizer.add(ImageCanvas)` register the dedicated scene + pane.  Uniforms and
overlay changes must **not** re-send image bytes.

## Files

- Edit: `py/pytanga/viz/serializer.py` (pass through `kind:"image"`)
- Edit: `py/pytanga/viz/server.py` (route `image_update`, binary push on image)
- Edit: `py/pytanga/viz/_scene_handle.py` (image scene + binary send glue)
- Edit: `py/pytanga/viz/visualizer.py` (`add(ImageCanvas)` polymorphism)
- New: `py/tests/viz/test_image_canvas_integration.py`

## Steps

- [x] **7.1 — serializer**
  - Ensure `serialize_scene_update`/`full_state` emit `kind:"image"` entities
    unchanged (they already pass through unknown kinds; add explicit handling if
    any normalizer would mangle the `shader`/`uniforms`/`images` fields).

- [x] **7.2 — server routes**
  - Add an `image_update` outbound path (uniform patch) and a `push_image_bytes`
    path; `set_image`/`add_image` trigger exactly one binary frame (via Phase 5
    `encode_image_frame`), while `set_uniform` triggers only the JSON
    `image_update` message.

- [x] **7.3 — `Visualizer.add(ImageCanvas)`**
  - Register the dedicated scene, add the image plane + overlay group, and
    return a handle; `scene_view()` composes with `SplitView` like any scene.

- [x] **7.4 — no-re-transmit invariant**
  - Add a test/assert that a uniform change and an overlay change produce no
    new binary frame (only JSON), and that `set_image` produces exactly one
    binary frame.

- [x] **7.5 — integration tests**
  - `py/tests/viz/test_image_canvas_integration.py`: add canvas → entity present;
    `set_uniform` → `image_update` payload; `set_image` → one binary frame.

## Validation

`uv run pytest py/tests/viz/test_image_canvas_integration.py py/tests/viz/test_image_canvas.py -q && uv run ruff check py/pytanga/viz/serializer.py py/pytanga/viz/server.py py/pytanga/viz/_scene_handle.py py/pytanga/viz/visualizer.py`

## Notes

- Follow the `visualizer.py` "add is polymorphic" rule: `ImageCanvas` is not a
  `View`, so it routes to the scene/`add_scene` path, not the overlay path.
- Keep the image binary send on the same server loop via
  `run_coroutine_threadsafe`, mirroring `push_raw`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.

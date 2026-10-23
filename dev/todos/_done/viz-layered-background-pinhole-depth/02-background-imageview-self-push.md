# Phase 2 — Background `ImageView` self-push + stable-index removal

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("Image background", and the
> `set_layout` push-callback injection in "Data flows").  This phase adds an
> opt-in binding seam on `ImageView` mirroring the existing `view._push` pattern.

## Goal

Let an `ImageView` used as `CameraView.background_image` push its own granular
updates once it is attached to a registered `SceneView`, and add stable-index
layer removal (`remove_layer(i)` / `set_layer(i, None)`).  Before binding the
mutators stay local-only (unchanged behavior); after binding they emit the
existing `view_background_uniforms` / `view_background_image` messages and only
the changed layer's pixel frame.

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `js/tanga-viewer.js` (regenerated)
- Edit: `py/tests/viz/test_image_background.py` (extend `_FakeTransport` cases)

## Steps

- [x] **2.1 — Stable-index storage in `ImageView`**
  - Change `self._images` to `list[ImageData | None]`.
  - `images` property returns `[img for img in self._images if img is not None]`;
    `primary_image` returns the first non-None entry (or `None`).
  - `serialized_images()` keeps slot positions: emit `None` for cleared slots;
    `_serialize_image(image, index)` guards on `None`.
  - `_check_layer_index(index)` keeps working against the slot list length.

- [x] **2.2 — `remove_layer` / `set_layer(i, None)`**
  - Add `remove_layer(index) -> None`: raise `ValueError` for `index == 0`
    (replace the primary via `set_image`); else set `_images[index] = None` and
    `u_layer{index}_enabled = 0`; call the push hook.
  - Make `set_layer(index, image, style=...)` accept `image=None` and delegate to
    `remove_layer(index)`.

- [x] **2.3 — Binding + push hook**
  - Add `ImageView._bind_background(transport, view_id, record_frame)` /
    `_unbind_background()`; store `_transport`, `_view_id`, `_record_frame`.
  - `record_frame(image_id, frame_or_none)` is a `LayoutHost`-supplied callback
    that updates/removes the reconnect frame cache entry.
  - Mutators, after mutating local state, call an internal `_push_background_*`:
    - uniform changes (`set_layer_style`, `set_uniform`) → one
      `view_background_uniforms` message with the diff (no pixel bytes);
    - pixel changes (`set_image`, `add_layer`, `set_layer`, `remove_layer`) → the
      changed layer's `encode_image_frame` bytes + one `view_background_image`
      message carrying `self` meta; `record_frame` is called for the changed id
      (or `None` to prune on removal).
  - No-op when unbound (guards on `_transport is None`).

- [x] **2.4 — `ImageView` emits its own background metadata**
  - Add `ImageView.background_meta()` (or reuse `_serialize_state()`) that returns
    the flat primary-image fields (`id/width/height/channels/dtype/source/…`) plus
    `images`/`shader`/`uniforms`/`max_layers` — matching `_image_view_meta()` —
    so `ImageView` can emit `view_background_image` without importing
    `views._helpers` (avoids a circular import).

- [x] **2.5 — Bind on layout registration**
  - In `_layout.set_layout`, after the existing `iter_scene_views` walk, bind each
    `camera_view.background_image` that is an `ImageView`
    (`image_view._bind_background(self._transport, scene_view.id,
    self._record_background_frame)`); unbind/ignore stale ones.
  - Add `LayoutHost._record_background_frame(image_id, frame_or_none)` updating
    `_background_frames` / `_background_versions` (or pruning).
  - In `push_background_image`, after wrapping/swapping, bind the resulting
    `ImageView` the same way.
  - Refactor `push_background_uniforms` / `push_background_image` so their logic
    is reusable by the bound path (or keep them as the manual `Visualizer` API,
    now documented to also accept an `ImageView`).

- [x] **2.6 — Frontend null-layer handling**
  - In `image-background.js`, in `createImageBackground` and
    `updateImageBackground`, skip `null` layer entries (set `uImage{i}` to
    `null`, leave `u_layer{i}_enabled = 0`) so stable-index cleared slots stay
    aligned with `uImage{i}`.
  - Rebuild `js/tanga-viewer.js`.

- [x] **2.7 — Tests**
  - After attaching (fake transport), `bg.set_layer_style(1,
    ImageLayerStyle(opacity=0.3))` → exactly one `view_background_uniforms`
    message containing `u_layer1_opacity`.
  - `bg.set_layer(1, image)` → exactly one binary frame (decode; assert id) and
    no frames for the other layers; one `view_background_image` message.
  - `bg.remove_layer(1)` / `bg.set_layer(1, None)` → updated meta with a `null`
    `images[1]`, `u_layer1_enabled == 0`, and pruned cache; `remove_layer(0)`
    raises.
  - Mutators before binding emit nothing.

## Validation

```
uv run pytest py/tests/viz/test_image_background.py py/tests/viz/test_image_view.py -q
uv run ruff check py/pytanga/viz/_image_view.py py/pytanga/viz/_layout.py
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py
```

## Notes

- Keep `Visualizer.set_background_image(view, ImageData|ImageView|None)` working
  and update its docstring to document the `ImageView` argument (the issue asks
  for this explicitly).
- The `ImageView` push path mirrors `ImageCanvas._push_uniforms` / `_sync_image`
  but uses `view_background_*` messages and the `view_id` instead of `scene`/`id`.

# Phase 4 — Camera image background (NDC quad)

## Goal

Add `SceneView(background_image=ImageData(...))` so one pane renders the camera
image as a screen-space NDC background behind the 3D scene. The image bytes
reuse the existing binary frame transport; the quad ignores the camera
(`gl_Position` set in clip space directly), so it always fills the pane exactly
and 3D content draws on top.

## Files

- New: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `py/pytanga/viz/views.py` (`SceneView.background_image` + serialize)
- Edit: `py/pytanga/viz/templates/views/three-view.js` (mount background quad)
- Edit: `py/pytanga/viz/_image_wire.py` / server send path (send bytes for the bg image id)
- New: `py/tests/viz/test_image_background.py`

## Steps

- [x] **4.1 — `SceneView.background_image`**
  - Add `background_image: ImageData | None = None` to `SceneView.__init__`
    (lazy/typing import of `ImageData`).
  - In `_serialize`, emit `result["background_image"]` with
    `{id, width, height, channels, dtype, source, url?}` when set
    (mirror `ImageView`'s metadata shape; `dtype` = `ImageDType` int code).

- [x] **4.2 — `image-background.js`**
  - `createImageBackground(imageMeta)` builds a `THREE.Mesh(PlaneGeometry(2,2),
    ShaderMaterial)` whose vertex shader writes `gl_Position = vec4(position.xy,
    0.999999, 1.0)` and fragment samples the texture (reuse `image.js`
    texture-building / `image-frames.js` `takeImageFrame`, plus the
    brightness/contrast uniforms if convenient).
  - Set `renderOrder = -1`, `frustumCulled = false`,
    `material.depthTest = material.depthWrite = false`, and add to the scene.

- [x] **4.3 — send bytes for the background image**
  - Reuse `_image_wire.encode_image_frame` + `Transport.send_bytes` to send the
    pixel buffer keyed by `imageMeta.id` when the layout is built/pushed (so
    `image-frames.js` has the frame when `ThreeJsView` mounts the quad).

- [x] **4.4 — mount in `ThreeJsView`**
  - When constructing/updating the pane from its scene_view node, if
    `background_image` is present, create the background quad (once) and add it;
    clear it in `clearOverlays()`/dispose paths so a layout re-push doesn't
    double-mount.

- [x] **4.5 — tests**
  - `test_image_background.py`: `SceneView(background_image=...)` serializes the
    metadata; missing/None omitted; `ImageData` dtype→int code mapping correct.

## Validation

`uv run pytest py/tests/viz/test_image_background.py -q && node --check py/pytanga/viz/templates/renderers/image-background.js && uv run python tools/build-viewer-js.py --check`

## Notes

- The quad fills the pane in clip space, so a projected point `(u,v)` lands on
  image pixel `(u,v)` only when the camera's aspect equals `W/H`. The example
  (phase 6) documents sizing the pane to the image aspect (or accepting stretch).
- `image-frames.js` already exports `takeImageFrame`/`hasImageFrame`; reuse them
  rather than re-implementing frame storage.
- URL images (`ImageData.url`) are supported by the metadata contract but can be
  a follow-up; data buffers are the tested path.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.

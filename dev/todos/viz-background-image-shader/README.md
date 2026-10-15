# Background image shaders + uniforms — Overview

**Created:** 2026-10-15 | **Status:** Done | **Branch:** `feat/bg-image-shader`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the
> "Image canvas (extension recipe)" and "Camera view (extension recipe) / Image
> background" sections) for the subsystem(s) this work touches, so the new code
> aligns with the documented architecture.  This work **extends** the documented
> `CameraView.background_image` contract and adds a new granular message, so the
> developer docs must be updated in Phase 6.

## Goal

Bring the `ImageCanvas` shader/uniform capability to the calibrated
`CameraView.background_image`, and do it by **unifying the shader/uniform state
model and the default-shader + JS helpers** between the two, while keeping two
renderers (scene mesh vs. NDC quad).  Concretely:

- The calibrated background renders with a **default brightness/contrast (and
  value-range) shader**, just like the image canvas.
- Users can **register a custom shader** and **access/modify its uniforms** for a
  background image.
- **Ctrl + left-drag** adjusts brightness (vertical) / contrast (horizontal) in
  `py/examples/apps/calibrated_labeling_app.py`, matching the image-canvas demos
  via a **backend round-trip** (`DragBinding` → Python handler → uniform message).

## Architecture (short)

Option A from the design discussion: **unify the model, keep two renderers.**

- **Shared model** — reuse `ImageView` (`py/pytanga/viz/_image_view.py`), which
  already owns `images` + `uniforms` + `fragment`/`vertex`.  Split its
  serialization so the *same state* can be emitted as the scene `image` entity
  (canvas) or as `background_image` metadata (background).  `CameraView.background_image`
  becomes an `ImageView` (a bare `ImageData` is auto-wrapped for backward
  compatibility).
- **Shared default shader** — extract the color pipeline (value-range normalize →
  brightness/contrast → clamp) from `image-shader.js::buildImageFragment` into a
  shared GLSL snippet.  `image.js` uses it verbatim; `image-background.js`
  *wraps* it with its letterbox/crop UV block.
- **Shared JS helpers** — `buildUniforms` and `applyImageUniforms` from
  `renderers/image.js` become shared, used by both renderers.
- **Two renderers** stay separate because they differ in render topology and
  framing: `image.js` (scene-entity mesh, camera-projected) vs.
  `image-background.js` (full-viewport NDC quad, camera-independent).

## Fixed contract (decided up front — later phases implement against this)

### `background_image` metadata (in `scene_view.camera_view.background_image`)

The existing `_image_meta` shape gains two additive fields:

```json
{
  "id": "camera", "width": 640, "height": 480, "channels": 3, "dtype": 0,
  "source": "data", "version": "<uuid>",
  "shader":   { "fragment": null, "vertex": null },
  "uniforms": { "u_brightness": 0.0, "u_contrast": 1.0, "u_midpoint": 0.5,
                "u_value_min": 0.0, "u_value_max": 255.0, "u_mode": 1 }
}
```

- `shader.fragment`/`shader.vertex` are `null` → use the default background shader.
- `uniforms` are seeded from the standard defaults + the image dtype/channels
  (`u_value_min`/`u_value_max`/`u_mode`), mirroring `ImageView`'s seeding.
- Any extra key is a custom uniform, exactly like the `image` entity.

### New granular uniform message

```json
{ "type": "view_background_uniforms", "view_id": "<view id>", "uniforms": { "u_contrast": 1.2 } }
```

Routed at view level (like `view_background_image`/`view_surface`), merged into
the background quad's `ShaderMaterial.uniforms` via the shared `applyImageUniforms`.
Never re-sends pixels and never re-pushes the layout.

### Public Python API (on `Visualizer`, mirroring `set_background_image`)

```python
viz.register_background_shader(view, fragment, vertex=None)
viz.register_background_uniform(view, name, default)   # setdefault semantics
viz.set_background_uniform(view, name, value)          # set + push granular message
```

`view` is a `SceneView` in a registered layout.

## Decisions (confirmed)

- **Backend round-trip for ctrl+drag** — a `DragBinding(MouseButton.LEFT, handler,
  ModifierKey.CTRL)` on the calibrated `InteractionSurface`; the handler computes
  the new uniform and calls `set_background_uniform`.  No frontend-local mutation.
- **Reuse `ImageView` as the shared model** (not a new parallel class).  It already
  holds images + uniforms + shader; only its serialization is split.
- **`set_background_image(view, image)` preserves shader/uniform state** when given
  a bare `ImageData` — it swaps only the pixels, so brightness/contrast and any
  custom shader survive an image swap (the app's "Noise image" checkbox).
- **Shader-source change requires a material rebuild** — `register_background_shader`
  re-pushes the background (`view_background_image` with the new `shader`), and
  `ThreeJsView.setBackgroundImage` gains a rebuild branch when the fragment/vertex
  changed.
- **Default background shader mirrors the image canvas** — value-range normalize →
  brightness/contrast → clamp, composed *after* the letterbox/crop UV math.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-shared-shader-model.md](./01-python-shared-shader-model.md) | Split `ImageView` serialization; `CameraView.background_image` carries an `ImageView` + serializes `shader`/`uniforms` |
| 2 | [02-server-background-uniform-plumbing.md](./02-server-background-uniform-plumbing.md) | `view_background_uniforms` message + public `Visualizer` API + shader/uniform threading |
| 3 | [03-frontend-default-shader-and-shared-helpers.md](./03-frontend-default-shader-and-shared-helpers.md) | Shared GLSL color pipeline + shared `buildUniforms`/`applyImageUniforms` + default background shader |
| 4 | [04-frontend-uniform-patch-and-rebuild.md](./04-frontend-uniform-patch-and-rebuild.md) | Dispatch `view_background_uniforms`; `setBackgroundUniforms`; shader-rebuild branch |
| 5 | [05-calibrated-labeling-app-ctrl-drag.md](./05-calibrated-labeling-app-ctrl-drag.md) | Ctrl+left-drag brightness/contrast in `calibrated_labeling_app.py` |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Developer docs + user docs + branch changelog |

## Testing as you go

- `uv run pytest py/tests/viz/test_image_view.py py/tests/viz/test_image_background.py -q` (phases 1–2)
- `uv run pytest py/tests/viz -q` (full viz regression, before merge)
- `node js/dev/tests/check-syntax.mjs` (frontend syntax gate, phases 3–4)
- `node --test js/dev/tests/*.test.mjs` (JS unit tests, phases 3–4)
- `uv run pytest py/tests/viz/test_background_surface.py py/tests/viz/test_interaction_surface.py -q` (phase 5)
- `uv run mkdocs build --strict` (phase 6)
- Manual browser smoke: `uv run python py/examples/apps/calibrated_labeling_app.py` (phases 4–5)

## Non-goals

- No merge of the two renderers into one code path — the scene-entity mesh and the
  NDC background quad keep their separate render/framing logic.
- No frontend-local uniform mutation; all uniform changes go through the backend.
- No change to the binary image-frame wire format or the `view_layout` shape
  (`background_image` metadata gains only additive `shader`/`uniforms` fields).
- No new `ImageCanvas` API surface — the canvas already supports shaders/uniforms;
  this plan only *shares* its model/shaders/helpers with the background.


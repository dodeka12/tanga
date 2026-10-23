# Layered background self-push + per-layer colormap + pinhole depth — Overview

**Created:** 2026-10-19 | **Status:** Done | **Branch:** `feat/improve-image-views`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the
> "Image canvas (extension recipe)", "Image background", and "New entity kind"
> sections).  This work **extends** three documented contracts — the background
> `ImageView` push path, the `image` layer shader (`max_layers` + per-layer
> colormap), and the `depth_image` mesh payload (pinhole intrinsics) — so the
> developer docs must be updated in Phase 6.

## Goal

Deliver three improvements to the viz image/depth subsystem, reported together
in `_input/pytanga-issue.md`:

1. A background `ImageView` that, once attached to a registered `SceneView`,
   pushes its **own** granular updates (uniform patches and per-layer pixel
   frames) instead of requiring `Visualizer.set_background_image` /
   `set_background_uniform`.  Layers are removed/cleared **in place** (stable
   index), and the layer count is raised to **8, dynamically** (single source of
   truth, ready to adopt the system's real `MAX_TEXTURE_IMAGE_UNITS` later).
2. Verify and document 4-channel RGBA alpha compositing, and add an optional
   **built-in per-layer colormap** (gray/viridis/turbo) for 1-channel layers.
3. A **pinhole camera mode** for `DepthImage`, specified the same way the
   calibrated background camera is (`CameraCalibration` → `PinholeCamera`), with
   `depth_kind="z"|"range"` and option **(b)** `apply_pose=True` (a
   `CameraCalibration` optionally auto-applies `camera_to_world()`).

## Architecture (short)

- `ImageView` (`_image_view.py`) is today pure data; `ImageCanvas` drives its own
  push.  Phase 2 adds an **opt-in binding** (`_bind_background(transport,
  view_id)`) that `LayoutHost.set_layout` injects while walking the scene views
  (mirroring the existing `view._push = …` injection in `LayoutHost.register`),
  so the background `ImageView` mutators emit the already-existing
  `view_background_image` / `view_background_uniforms` messages themselves.
- The image layer shader is generated in `renderers/image-shader.js` (shared by
  the scene plane and the NDC background quad) and looped over a hard-coded `4`
  in `renderers/image.js` and `renderers/image-background.js`.  Phase 1 makes
  the layer count a serialized `max_layers` field, defaulting to 8.
- `DepthImage` (`depth_image.py`) stays a pure data model; Phase 4 adds
  `DepthImageStyle.camera` / `depth_kind` / `apply_pose` and emits a `mesh.camera`
  block that `renderers/depth-image.js` consumes to build camera-frame vertices.

## Fixed contract (decided up front — later phases implement against this)

### 1. Layer count (`max_layers`)

- Python: replace `MAX_IMAGE_LAYERS = 4` with `DEFAULT_MAX_IMAGE_LAYERS = 8`
  (keep `MAX_IMAGE_LAYERS` as an alias for one release).  `ImageView.__init__(…,
  *, max_layers=DEFAULT_MAX_IMAGE_LAYERS)` stores it; `add_layer` checks against
  `self._max_layers`.
- Serialize `"max_layers": <int>` in both `ImageView._serialize_state()`
  (the `image` entity) and `_image_view_meta()` (`views/_helpers.py`, the
  background metadata).
- Frontend reads `ent.max_layers ?? 8` (scene) / `imageMeta.max_layers ?? 8`
  (background); `buildImageLayerPipeline(layerCount)`,
  `buildLayerUniforms(u, layerCount)`, and every `i < 4` loop become
  `i < layerCount`.

### 2. Background self-push + stable-index removal

- `ImageView._images` becomes `list[ImageData | None]` of stable slots.
  `remove_layer(i)` and `set_layer(i, None)` clear in place (set the slot to
  `None` and `u_layer{i}_enabled = 0`); **no index shifting**.  Removing layer 0
  (the frame-defining primary) raises `ValueError` (replace it with `set_image`).
- `ImageView.images` / `primary_image` return the **non-None** images;
  `serialized_images()` returns a fixed-length list with `None` (JSON `null`)
  for cleared slots so the frontend keeps `images[i]` ↔ `uImage{i}` aligned.
- Mutators push only when bound:
  - `set_layer_style(i, style)` → one `view_background_uniforms` message with the
    diff (`{u_layer{i}_…}`).
  - `set_image` / `add_layer` / `set_layer` / `remove_layer` / `set_layer(i,
    None)` → the changed layer's binary frame (via `encode_image_frame`) followed
    by one `view_background_image` message with `_image_view_meta(...)`; the
    `_background_frames` / `_background_versions` caches are updated for the
    changed id only and pruned on removal.
  - `set_uniform(name, value)` → one `view_background_uniforms` message.

### 3. Per-layer colormap + RGBA alpha

- New `ImageColormap` enum in `image.py`: `GRAY=0`, `VIRIDIS=1`, `TURBO=2`
  (mirroring `DepthColormap` codes).  `ImageLayerStyle.colormap:
  ImageColormap | str | None = None`.
- Uniform `u_layer{i}_colormap` (int, default `0`) is seeded in
  `_apply_layer_style` / `_merge_layer_style` and projected into `images[i]`.
- Shader (`image-shader.js`): `tangaSampleLayer` returns `vec4` (rgb + a) where
  `a = tex.a` for 4-channel layers else `1.0`; `tangaComposite` blends with
  `u_layer{i}_opacity * a`.  For scalar channel modes (gray/magnitude/alpha), the
  normalized value is mapped through `buildImageColormap()` using
  `u_layer{i}_colormap`.

### 4. Depth pinhole camera

- `DepthImageStyle.camera: CameraCalibration | PinholeCamera | None = None`,
  `depth_kind: str = "z"` (validated `"z"|"range"`), `apply_pose: bool = True`.
- Intrinsics are resolved from `K` (`CameraCalibration`) or `fx/fy/cx/cy`
  (`PinholeCamera`).  `DepthImage._build` emits
  `mesh.camera = {fx, fy, cx, cy, depth_kind}` and, when `apply_pose` and the
  camera is a `CameraCalibration`, `mesh.camera_to_world` (16 floats from
  `calib.camera_to_world()`).
- Camera-frame vertices (x right, y down, z forward): `z = (depth −
  depth_offset) · depth_scale`; `X = (u−cx)/fx · z`; `Y = (v−cy)/fy · z`; for
  `depth_kind="range"`, `z = range / √(((u−cx)/fx)² + ((v−cy)/fy)² + 1)`.
  `world_scale` is ignored in this mode; normals, segmentation selection, and
  plain/image/depth render modes keep working.

## Decisions (confirmed)

- **Depth camera = `CameraCalibration` / `PinholeCamera`** (the same classes the
  calibrated background image uses), **not** a reintroduced `PinholeIntrinsics`.
- **Option (b)** for world placement: a `CameraCalibration` **optionally
  auto-applies** its `camera_to_world()` pose (`apply_pose=True` default); the
  surface remains a transformable entity.
- **Stable index** layer removal (clear in place, no re-index).
- **8 layers default**, implemented **dynamically** via a serialized `max_layers`
  (single source of truth in Python), so the frontend can later adopt
  `gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS)`.
- **Built-in colormap first**; the per-layer LUT *texture* path is a non-goal.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-dynamic-layer-count.md](./01-dynamic-layer-count.md) | `max_layers` (8) model + serialization + frontend loops |
| 2 | [02-background-imageview-self-push.md](./02-background-imageview-self-push.md) | Bind background `ImageView`; granular pushes; stable-index removal |
| 3 | [03-per-layer-colormap.md](./03-per-layer-colormap.md) | RGBA alpha verification/fix + built-in per-layer colormap |
| 4 | [04-depth-pinhole-camera.md](./04-depth-pinhole-camera.md) | `DepthImageStyle.camera` + `depth_kind` + `apply_pose` + frontend geometry |
| 5 | [05-examples.md](./05-examples.md) | Adapt `image_layers.py` + `calibrated_labeling_app.py`; add `pinhole_depth.py` |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Developer docs + user docs + branch changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression (each phase adds its tests).
- `uv run ruff check .` and `uv run ty check` — lint + type gates.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests.
- `uv run python tools/build-viewer-js.py` — rebuild the committed viewer bundle after template edits.
- `uv run mkdocs build --strict` — docs gate (Phase 6).
- `uv run python tools/generate-example-docs.py` (then `--check`) — examples gallery (Phase 5).

## Non-goals

- No per-layer LUT *texture* upload (built-in colormap only).
- No distortion support in the pinhole depth mode (images are rectified).
- No merge of the scene-plane and NDC background-quad renderers.
- No runtime query of `MAX_TEXTURE_IMAGE_UNITS` yet (the seam is ready, the query
  is a later follow-up).

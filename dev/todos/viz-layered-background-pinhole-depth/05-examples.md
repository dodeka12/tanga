# Phase 5 — Examples (adapt + add)

> **Architecture note — check the developer docs.** No architecture change here;
> examples must follow `dev/workflows/example-docs.md` (description + `Run with:`
> + `Keywords:` header) and `docs/dev/architecture/viz-architecture.md` where
> they exercise the image/depth renderers.

## Goal

Update the examples that exercise the changed APIs and add the required pinhole
depth example, so the new behaviors (background self-push, per-layer colormap,
pinhole depth) are demonstrated and manually testable.

## Examples adapted (modified) — re-test these

- **`py/examples/viz/image/image_layers.py`** — add a per-layer **colormap**
  dropdown for the uint16 depth layer (demonstrates `ImageLayerStyle(colormap=…)`
  on a 1-channel layer).  Keep the existing enable/opacity/blend controls.

- **`py/examples/apps/calibrated_labeling_app.py`** — switch the background
  brightness/contrast handler from `viz.set_background_uniform(view, …)` to the
  bound background `ImageView.set_uniform(...)`, and the "Noise image" swap from
  `viz.set_background_image(left, …)` to `bg.set_image(...)` (demonstrates the
  self-push pattern this work enables).

## Example added (new) — re-test this

- **`py/examples/viz/image/pinhole_depth.py`** — build a depth map from a
  `CameraCalibration` (as in `py/examples/viz/camera/pinhole_calibrated.py`),
  render it via `DepthImageStyle(camera=calib, depth_kind="z")` in a world scene
  next to a known object (e.g. a `Frustum` / bounding box), using `apply_pose=True`
  so the surface lands at its true world pose.  Follow `dev/workflows/example-docs.md`
  (description + `Run with:` + `Keywords:` header).

## Verified unaffected (no change; no re-test required, but listed for completeness)

- `py/examples/viz/image/depth_surface.py` — orthographic default unchanged.
- `py/examples/viz/lighting/scene_lighting.py` — plain-lit depth surface unchanged.
- `py/examples/viz/camera/pinhole_calibrated*.py`, `pinhole_overlay.py` — single-image
  background path unchanged (still work via `set_background_image`).
- `py/examples/viz/image/{image_canvas,raw_image,standard_image,huge_image,load_image_from_disk,custom_shader_rgb_rotate}.py` —
  unaffected by these changes.

## Steps

- [x] **5.1 — `image_layers.py` colormap control**
  - Import `ImageColormap`; add a `DropdownView` per layer (at least the depth
    layer) with options `["gray", "viridis", "turbo"]` and a handler calling
    `canvas.set_layer_style(index, ImageLayerStyle(colormap=...))`.

- [x] **5.2 — `calibrated_labeling_app.py` self-push**
  - Keep a reference to the background `ImageView`; replace the
    `set_background_uniform` calls with `bg.set_uniform(...)` and the
    `set_background_image(left, background)` swap with `bg.set_image(background)`.
  - Confirm no behavior change (the handler still adjusts brightness/contrast live).

- [x] **5.3 — `pinhole_depth.py` new example**
  - Load/construct a `CameraCalibration` + a synthetic depth map (e.g. a
    `Z = constant` plane or a fronto-parallel ground plane); add a known object
    (Frustum or box corners) to the same `world` scene; show via
    `viz.new(depth, style=DepthImageStyle(camera=calib, depth_kind="z"))`.
  - Add the required docstring header per `dev/workflows/example-docs.md`.

- [x] **5.4 — Regenerate the example gallery**
  - `uv run python tools/generate-example-docs.py` then
    `uv run python tools/generate-example-docs.py --check`.

## Validation

```
uv run python tools/generate-example-docs.py --check
uv run ruff check py/examples/viz/image/image_layers.py py/examples/viz/image/pinhole_depth.py py/examples/apps/calibrated_labeling_app.py
```

Manual smoke (re-test after this phase):

```
uv run python py/examples/viz/image/image_layers.py
uv run python py/examples/viz/image/pinhole_depth.py
uv run python py/examples/apps/calibrated_labeling_app.py
```

## Notes

- The pinhole example is the Phase-4 acceptance example; it must show the depth
  surface next to a known object placed via the same `CameraCalibration`.
- Do not modify the "unaffected" examples unless a smoke test surfaces a real
  regression from Phases 1–4.

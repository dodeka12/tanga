# Viz Calibration Example — Overview

**Created:** 2026-09-22 | **Status:** Done | **Branch:** `feat/calib-cam-view`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add one self-contained, **offline and deterministic** example that bundles a
single real calibrated image plus its camera intrinsics/extrinsics and one
object's ground-truth 6D pose from **BOP**, and shows it in two panes — the
**left** pane is the calibrated camera view (the photo as the background image,
with the ground-truth shape projected pixel-accurately on top), the **right**
pane is the **world** view (the camera frustum + the same ground-truth shape in
3D, with the image/data source and license annotated).  The example reads only
bundled local files: no network at run time.

## Decisions (confirmed)

- **Data source:** BOP **T-LESS** (Hodan et al., *T-LESS: An RGB-D Dataset for
  6D Pose Estimation of Texture-less Objects*, WACV 2017), license **CC BY 4.0**.
  Bundling one real training image (public ground-truth pose) is
  license-compatible; we deliberately avoid LM-O/Linemod, whose original terms
  are restrictive and unsuitable for redistribution.
- **Offline / deterministic:** the image + calibration + GT pose are bundled in
  the repo; the example performs no runtime download and no network I/O.
- **Ground-truth "shape/position":** the object's 3D bounding box (from
  `models_info.json` `min_*`/`size_*`) rendered as a `Box` (wireframe) plus its
  8 corners as `Point`s, and a small coordinate frame at the GT pose — no
  mesh/PLY importer is added (out of scope; the viewer has none).
- **Image decode:** `pil_to_numpy` from `pytanga.viz.image` (PIL is already a
  dev dependency), producing an `ImageData` for `CameraView.background_image`.
- **Layout:** mirrors `py/examples/viz/camera/pinhole_overlay.py` — left
  `SceneView("world", camera_view=…)` with `navigation="2d"`, `viewport`, and
  `hide={frustum.id}`; right `SceneView("world")` with the default camera.
- **Attribution annotation:** the right (world) pane shows the image/data source
  and license as an overlay annotation — a `GroupView("Data", …)` containing a
  `LabelView`/`MarkdownView`, anchored `bottom-left` — so the provenance is
  visible in the view, not only in `ATTRIBUTION.md`.

## Contract (fixed)

Bundled under `py/examples/viz/camera/data/tless/`:

- `image.png` — the single T-LESS training image (`width × height × 3`, uint8).
- `calibration.json`:
  ```json
  {
    "image": "image.png",
    "width": 720,
    "height": 540,
    "K": [[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]],
    "R_w2c": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
    "t_w2c": [0.0, 0.0, 0.0],
    "obj_id": 1,
    "cam_R_m2c": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
    "cam_t_m2c": [0.0, 0.0, 0.0],
    "bbox_min": [0.0, 0.0, 0.0],
    "bbox_size": [0.0, 0.0, 0.0]
  }
  ```
  Conventions (OpenCV, matching `pinhole_camera`):
  - `K`, `R_w2c`, `t_w2c` are the world→camera intrinsics/extrinsics so a world
    point `X` projects to pixel `u = fx·(Xc/Zc)+cx`, `v = fy·(Yc/Zc)+cy` with
    `Xc = R_w2c·X + t_w2c` — fed verbatim to
    `pinhole_camera(K, R_w2c, t_w2c, image_size=(width, height))`.
  - `cam_R_m2c`, `cam_t_m2c` are the object's model→camera GT pose
    (`Xc = cam_R_m2c·X_model + cam_t_m2c`).
  - `bbox_min`/`bbox_size` are the object's 3D bbox in model coordinates (from
    BOP `models_info.json`).
- `ATTRIBUTION.md` — dataset citation + CC BY 4.0 notice.

The model→world transform used to place the GT box in Tanga's world frame is
derived from `R_w2c`/`t_w2c` and `cam_R_m2c`/`cam_t_m2c`:

```
R_m2w = R_w2cᵀ · cam_R_m2c
t_m2w = R_w2cᵀ · (cam_t_m2c - t_w2c)
```

so the GT box corners `p_model` map to world as `p_world = R_m2w·p_model + t_m2w`.

## Steps

- [x] **1 — Bundle the data**
  - Download the T-LESS base archive + one real training image from
    `bop-benchmark/tless` on HuggingFace; extract `scene_camera.json`,
    `scene_gt.json`, `models_info.json`, and a single real training image.
  - Pick one object instance; write `image.png` + `calibration.json` (the exact
    shape above) + `ATTRIBUTION.md` under `py/examples/viz/camera/data/tless/`.
  - Do **not** commit the full dataset archive — only the one image + minimal
    JSON + attribution.

- [x] **2 — Example**
  - New `py/examples/viz/camera/pinhole_calibrated.py` mirroring
    `pinhole_overlay.py`: load `calibration.json` + decode `image.png` via
    `pil_to_numpy`, build `pinhole_camera(K, R_w2c, t_w2c, image_size=(w, h))`,
    compute `R_m2w`/`t_m2w`, add the GT `Box` + corner `Point`s + a coordinate
    frame + the `Frustum.from_camera(cam, …)` to the shared scene.
  - Left pane = `SceneView("world", camera_view=CameraView(cam,
    navigation="2d", viewport=ViewportConfig(zoom=1.0, pan=(0,0)),
    background_image=ImageData(...)), hide={frustum.id})`.
  - Right pane = `SceneView("world", overlay=[GroupView("Data",
    [LabelView("attribution", value="Image & data: T-LESS (Hodan et al.,
    WACV 2017), BOP benchmark — License: CC BY 4.0")], position="bottom-left")])`
    — the world view carries the source + license annotation.
  - Header per `dev/workflows/example-docs.md`: `<name>.py — …` first line,
    `Run with:` line, and a trailing `Keywords:` line (e.g.
    `Keywords: camera, pinhole, calibration, BOP, image background, frustum, split view, annotation`).

- [x] **3 — Data-validation test**
  - New `py/tests/viz/test_calibration_example_data.py` that loads the bundled
    `calibration.json` and asserts: `K` is 3×3 with `fx≈fy>0`, `R_w2c` is 3×3
    orthonormal, `t_w2c` has shape `(3,)`, `cam_R_m2c` is orthonormal,
    `bbox_size` is strictly positive, `image.png` exists and decodes to the
    declared `width`/`height`.

- [x] **4 — Docs + changelog**
  - Regenerate the example gallery: `uv run python tools/generate-example-docs.py`.
  - Add a changelog entry under `docs/changelog/` per
    `dev/workflows/changelog.md`.

## Validation

- `uv run pytest py/tests/viz/test_calibration_example_data.py -q`
- `uv run ruff check py/examples/viz/camera/pinhole_calibrated.py`
- `uv run python tools/generate-example-docs.py --check`
- `uv run mkdocs build --strict`
- Manual smoke (live browser, not CI): `uv run python
  py/examples/viz/camera/pinhole_calibrated.py` — left pane shows the photo with
  the GT box projected on it; right pane shows the frustum + GT box in 3D.

## Non-goals

- No mesh/PLY importer (render only the GT bbox + corners + frame).
- No runtime network/download.
- No change to the pinhole/calibration core (already implemented on this branch).

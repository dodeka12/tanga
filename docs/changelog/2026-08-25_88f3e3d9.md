# Changes since version 1.2.0

## New Features

- **Per-frame camera playback in animated HTML export** — `AnimationRecording`
  now snapshots the scene camera at each frame, and the animated export playback
  applies it via a shared `applyCameraConfig` helper, so `set_camera()` inside an
  animation loop is reflected in the exported animation.

## Bug Fixes

- **Default 2D view now uses an orthographic camera** — a `space_dim=2` scene
  without an explicit camera kept the initial perspective camera, so
  `flush(fit_camera=True)` recentered a perspective camera and made the
  depth-layered grid and axes misalign. The viewer now switches to a top-down
  orthographic camera (see `py/examples/viz/camera/fit_2d.py`).

- **HTML export now honors the live scene camera** — the export bootstrap dropped
  the 2D camera rectangle (`xmin/xmax/ymin/ymax`, `uniform`, `border_px`) and the
  3D `up` vector, and animated figure exports always rendered in 3D. Exports now
  apply the full camera config through the shared `applyCameraConfig` helper.

## Refactor

- **Reorganized the viz examples** — moved `py/examples/viz/*.py` into topic
  subfolders (`camera/`, `plotting/`, `entities/`, `labels/`, `animation/`,
  `interaction/`, `scenes/`, `export/`, `styling/`) and dropped the `demo_`
  filename prefix, with the docs index updated to match.

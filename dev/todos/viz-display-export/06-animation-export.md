# Phase 6 — Animated export via `animation=` keyword

**Status:** Done

## Goal

Move the recording factory to `Visualizer`/`VizSceneHandle` and fold the
animated export variants into `export_snapshot(..., animation=rec)` /
`export_figure(..., animation=rec)`. `AnimationRecording` stays unchanged as
the frame store.

## Files

- Modify: `py/pytanga/viz/export/_exporter.py`
- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`

## Steps

- [x] Add `animation=`/`anim_style=` to `Visualizer.export_snapshot` /
      `export_figure` (and scene helpers), dispatching to the animated
      renderers when set. `render_export_animated_*` remain internal
      implementations (kept as-is).
- [x] Add `Visualizer.start_animation_recording()` returning
      `AnimationRecording(scene, styles_map=scene.styles.kind)`.
- [x] Add `VizSceneHandle.start_animation_recording()` for its scene.
- [x] Add deprecated aliases `export_animated_html` / `export_animated_figure`
      on `SceneExporter`, delegating to the new `animation=` keyword.

## Unit tests

- [x] `py/tests/viz/test_export_static.py`:
  - [x] `start_animation_recording()` + `capture_frame()` +
        `export_snapshot(..., animation=rec)` writes a file.
  - [x] `export_figure(animation=rec)` returns a string.
  - [x] `export_animated_html` alias emits `DeprecationWarning`.

## Verification

- [x] `uv run pytest py/tests/viz/` passes (435 tests).

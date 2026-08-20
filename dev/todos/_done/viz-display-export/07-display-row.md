# Phase 7 — Jupyter `display()` and mixed `display_row()`

**Status:** Done

## Goal

Provide a symmetric `display()` (live iframe) on `Visualizer` and
`VizSceneHandle`, and generalize `display_row()` to accept live scenes and
static snapshots side by side.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/_jupyter.py`

## Steps

- [x] Add `Visualizer.display(width, height)` — live iframe of the main scene
      (mirrors `VizSceneHandle.display`).
- [x] `VizSceneHandle.display_snapshot` already exists (Phase 4); `display`
      (live) is symmetric.
- [x] Generalize `Visualizer.display_row(*scenes, mode="live"|"static")` — live
      entries embed the server URL, static entries embed a `srcdoc` snapshot.
- [x] Keep `_repr_html_` unchanged (auto-display via `viz` / handle).

## Unit tests

- [x] `py/tests/viz/test_display.py`:
  - [x] `viz.display()` returns an iframe with the server URL.
  - [x] `display_row((a, None), (b, None))` produces two live iframes.
  - [x] `display_row((a, None), (b, None), mode="static")` produces two srcdoc
        iframes.

## Verification

- [x] `uv run pytest py/tests/viz/` passes (438 tests).

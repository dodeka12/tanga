# Phase 7 — Jupyter `display()` and mixed `display_row()`

**Status:** Planned

## Goal

Provide a symmetric `display()` (live iframe) on `Visualizer` and
`VizSceneHandle`, and generalize `display_row()` to accept live scenes and
static snapshots side by side.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/_jupyter.py`

## Steps

- [ ] Add `Visualizer.display(width, height)` — live iframe of the main scene
      (mirror the existing `VizSceneHandle.display`).
- [ ] Ensure `VizSceneHandle.display_snapshot(width, height)` exists (from
      Phase 4) and that `display()` (live) is symmetric.
- [ ] Generalize `Visualizer.display_row(*scenes, …)` so each entry is either
      a live `VizSceneHandle` (server URL) or a static snapshot (iframe
      `srcdoc`), rendering both in the flex row.
- [ ] Keep `_repr_html_` unchanged (auto-display via `viz` / handle).

## Unit tests

- [ ] `py/tests/viz/test_display.py`:
  - [ ] `viz.display()` returns an iframe with the server URL.
  - [ ] `display_row((handle_a, None), (handle_b, None))` produces two iframes.

## Verification

- [ ] `uv run pytest py/tests/viz/test_display.py` passes.
- [ ] Manual: Jupyter — live and static scenes stack side by side without
      style leakage.

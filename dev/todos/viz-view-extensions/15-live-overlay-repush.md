# Phase 15 — Live overlay re-push (`server.py` + `visualizer.py`)

## Goal

When overlays change (add/remove control group or menu) after a browser has
connected, re-serialize and re-push the correct `view_layout` to the affected
sessions. This is what makes `VisualizerApp` examples work — they call
`add_control_group` inside `init()`, i.e. after the browser received its layout.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/visualizer.py`

## Steps

- [x] **15.1 — `push_layout_to_session` (`server.py`)**
  - Add a helper that sends a `view_layout` payload to a single `BrowserSession`.

- [x] **15.2 — `_push_layout_updates` (`visualizer.py`)**
  - After `_sync_overlays`, for every connected session push the layout it should
    show: `_layout_callback(session.layout)` when `session.layout` is set, otherwise
    `_scene_layout_for(session.scene)`. Run on the server loop.

- [x] **15.3 — Trigger on overlay changes**
  - Call `_push_layout_updates` from `_sync_overlays` (and its async wrapper) so
    `add_control_group` / `add_menu` / `remove_*` / `clear_*` update live browsers.

- [x] **15.4 — Idempotent frontend rebuild**
  - Confirm `_buildLayout` (Phase 14.2) makes re-push safe: teardown before rebuild.

## Validation

`uv run pytest py/tests/viz/ -q && node --check py/pytanga/viz/templates/viewer.js`

## Notes

- Re-push must target the *session*, not broadcast: a single-scene tab gets its
  scene's layout; a layout tab gets its named layout.

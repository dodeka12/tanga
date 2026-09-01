# Phase 16 — Integration + examples

## Goal

Verify the unified mode end-to-end and confirm the existing single-scene examples
work without changes — their `add_control_group` calls (run in `init()`, after
connect) now appear via the live re-push.

## Files

- Edit (only if needed): `py/examples/viz/interaction/*.py`, `py/examples/viz/banners/heavy_work.py`
- Extend: `py/tests/viz/test_layout_api.py`, `py/tests/viz/test_server_layout.py`

## Steps

- [x] **16.1 — Example verification**
  - Confirm `all_controls.py`, `file_chooser.py`, `two_spheres_interact.py`, and
    `heavy_work.py` (all `VisualizerApp`, single-scene) still render their groups via
    the unified path; migrate any that need a layout (none expected).

- [x] **16.2 — `_myScene` / `navigate` / `_forMyScene`**
  - Reconcile the single-scene identity helpers (`_myScene`, `_forMyScene`) with the
    layout path so per-scene routing and `navigate` still work in both modes.

- [x] **16.3 — Regression tests**
  - Add a live-re-push test (fake server / fake session) asserting a single-scene
    session receives its scene's layout after an overlay change.

## Validation

`uv run pytest py/tests/viz/ -q`

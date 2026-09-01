# Phase 11 — Example: unified `add_control_group`

## Goal

Show the unified `add_control_group` API: an overlay-anchored group and an
optional group anchored to a 3D object, both now backed by `GroupView`.

## Files

- New: `py/examples/viz/scenes/control_group_overlay.py`
- (regenerate docs after adding the example)

## Steps

- [x] **11.1 — Example script**
  - Create `py/examples/viz/scenes/control_group_overlay.py` with the required
    header (one-line description, `Run with:`, `Keywords:` — see
    `dev/workflows/example-docs.md`).
  - Add a 3D object (e.g. a `Point`/`Sphere`) and create two groups via
    `add_control_group`: one overlay-anchored (`position="top-right"`) and one
    anchored to the object (`parent_id=<entity id>`), each with a slider/button.
  - Verify both render from the single `GroupView` path.

- [x] **11.2 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/scenes/control_group_overlay.py`

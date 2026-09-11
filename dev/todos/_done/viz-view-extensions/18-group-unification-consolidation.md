# Phase 18 — Group unification consolidation (single-scene + layout)

## Goal

Re-verify the `add_control_group` → `GroupView` facade (Phases 10–11) under the
unified view mode and extend its example so the single-scene path is demonstrated
too. This is a verification/consolidation pass, **not a redo** — Phases 12–15 make
the facade render in single-scene mode without changing its code.

## Files

- Edit: `py/examples/viz/scenes/control_group_overlay.py`
- Extend: `py/tests/viz/test_layout_api.py`

## Steps

- [x] **18.1 — Verify overlay + parent_id in single-scene mode**
  - Confirm `add_control_group(position=...)` (global overlay) and
    `add_control_group(parent_id=...)` (3D attach) render on a single-scene URL
    (`/`, no `?view=`), not only via `show(layout=...)`.

- [x] **18.2 — Extend the group example**
  - Update `control_group_overlay.py` to also show the single-scene path (or add a
    sibling `control_group_single.py`), so the unified behavior is demonstrated
    without requiring `show(layout=...)`.

- [x] **18.3 — Regression tests**
  - Add tests asserting `_scene_layout_for("")` and `_scene_layout_for("<name>")`
    carry the `add_control_group` overlays (global, per-scene, and `parent_id`).

- [x] **18.4 — Docs consistency**
  - Ensure the `add_control_group` docs state it works in both modes (align with
    Phase 17.3).

## Validation

`uv run pytest py/tests/viz/test_layout_api.py -q && uv run ruff check py/examples/viz/scenes/control_group_overlay.py && uv run python tools/generate-example-docs.py --check`

# ActPolygon Ctrl+drag endpoint insert — plan

**Created:** 2026-10-15 | **Status:** Planned | **Branch:** `fix/polygon-ctrl-drag-endpoint`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Restore Ctrl+left-drag on an `ActPolygon` vertex handle so the gesture routes to
the vertex handler (insert a new vertex) instead of falling through to the
pane's interaction surface.  This regressed in PR #117 (`feat/bg-image-shader`),
whose exact trigger-modifier matching stopped the endpoint's modifier-less drag
trigger from matching Ctrl+drag (see
`docs/changelog/2026/10/15_70258d8b6.md`).

## Steps

- [x] **1.1 — Give polygon vertex handles a Ctrl drag binding.**
  - In `py/pytanga/viz/_active.py::ActPolygon._spawn_handles`, add
    `drag_bindings=[DragBinding(MouseButton.LEFT, self._make_vertex_handler(i), ModifierKey.CTRL)]`
    to each vertex `ActPoint`.
  - Update `py/tests/viz/test_act_polygon.py::TestHandleDragMode` so the
    unmodified `VIEW_PLANE` trigger is still asserted for every handle, and add
    a test asserting each vertex handle also emits a `DRAG` trigger with
    `modifiers == {ModifierKey.CTRL}` (drag mode `VIEW_PLANE`).

- [x] **1.2 — Changelog.**
  - Follow `dev/workflows/changelog.md`: add
    `docs/changelog/2026/10/DD_fix-polygon-ctrl-drag-endpoint.md` with a
    `## Bug Fixes` bullet describing the restored Ctrl+drag insert.

## Validation

`uv run pytest py/tests/viz/test_act_polygon.py -q`

## Non-goals

- No change to `ActLine`, other `Act*` handles, or the surface
  brightness/contrast behaviour — those keep falling through to the surface on
  Ctrl+drag.
- No frontend/template change and no bundle rebuild (trigger serialization is
  backend-only).

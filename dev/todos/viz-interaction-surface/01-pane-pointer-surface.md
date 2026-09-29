# Phase 1 — Per-pane pointer surface

## Goal

Add the per-pane pointer surface primitive: a `SceneView` pane can carry an
`InteractionSurface` (plane + `CoordinateMapper` + pointer handlers), the frontend
emits pointer events for the pane's empty space, and Python resolves them to
world positions on the plane.  Add `read_only` to suppress interaction per pane.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- New: `py/pytanga/viz/_surface.py` (or `_interaction_surface.py`)
- Edit: `py/pytanga/viz/views/scene_view.py`
- Edit: `py/pytanga/viz/templates/interaction.js`
- Edit: `py/pytanga/viz/templates/viewer.js` (wire the surface + `read_only` into `ThreeJsView`)
- Edit: `py/pytanga/viz/__init__.py` (export `InteractionSurface`)
- New: `py/tests/viz/test_interaction_surface.py`

## Steps

- [ ] **1.1 — `InteractionSurface` class**
  - A `mapper: CoordinateMapper` + `on_drag_start`/`on_drag`/`on_drag_end`/
    `on_click` handlers; `serialize()` returns `{"point": …, "normal": …}` from
    `mapper.plane()` plus a stable surface id.
- [ ] **1.2 — `SceneView.surface` + `SceneView.read_only`**
  - Accept `surface=` and `read_only=`; serialize `"surface"` and `"read_only"`
    into the `scene_view` node; register the surface's handlers in the `(id,
    event)` registry (`origin=INTERACTION`).
- [ ] **1.3 — Frontend: emit surface pointer events on empty space**
  - In `interaction.js`, when `_getInteractiveHit` finds no entity but the pane
    has a surface, start a surface drag/click (reuse the existing ray↔plane
    intersection with the surface's `{point, normal}`) and send the same
    `interaction:drag_start/drag_move/drag_end/click` messages with the surface
    id and the pane camera.
- [ ] **1.4 — Frontend: `read_only` pane**
  - When `read_only`, do not emit surface events and do not raycast `Act` objects
    (navigation/OrbitControls still work).
- [ ] **1.5 — Python dispatch + tests**
  - Route surface pointer events to the registered handlers (world position via
    `mapper.plane()` ray intersection).  Unit-test `InteractionSurface.serialize`
    and the ray↔plane resolution without a browser.

## Validation

```
uv run pytest py/tests/viz/test_interaction_surface.py -q && uv run ruff check . && uv run ty check && node js/dev/tests/check-syntax.mjs
```

## Notes

- Manual browser smoke is mandatory here: the flat `ImageCanvas` example must
  still pan/zoom/draw, and a read-only pane must orbit but not draw.
- The frontend already has per-pane `InteractionController` + ray↔plane drag; this
  phase is a localized addition, not a rewrite of `interaction.js`.

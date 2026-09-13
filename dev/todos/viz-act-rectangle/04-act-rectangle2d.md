# Phase 4 — `ActRectangle2D`

## Goal

An interactive axis-aligned rectangle: 4 square corner handles (resize) and an
optional translation handle (move).  Default behaviour is fully implemented but
overridable, mirroring `ActPoint`.  A small `ActPoint.set_position()` addition
lets the coordinator reposition handles programmatically.

## Files

- Edit: `py/pytanga/viz/_active.py` (add `ActPoint.set_position` + `ActRectangle2D`)
- Edit: `py/pytanga/viz/__init__.py` (export `ActRectangle2D`)
- New: `py/tests/viz/test_act_rectangle2d.py`

## Steps

- [x] **4.1 — `ActPoint.set_position(pos)`**
  - Sets `_point` and pushes the entity (`update()`) without flushing, so a
    coordinator can reposition many handles and flush once.  Closes the
    desync footgun in `_input/pytanga-actpoint-entity-setter-does-not-sync-drag-anchor.md`.

- [x] **4.2 — `ActRectangle2D(ActSceneObject)` model**
  - Constructor `(center, size=(w,h), *, show_translate_handle=True,
    handle_style=..., on_change=None, **act_kwargs)`.
  - `entity` → the `Rectangle2D`; `interaction_config` → `enabled=False` (the
    body is visual-only).
  - `_init(viz_handle, entity_id)`: `super()._init(...)`, then spawn 4 corner
    `ActPoint` handles (with `SquarePointStyle`, `drag_mode=XY_PLANE`,
    `handler=<corner closure i>`) and one translation `ActPoint` (center,
    `handler=<translate closure>`), each added via `viz_handle.add(...)`.
  - Track handle entity ids for removal; provide `remove()`/`clear()` that
    removes the body + handles.

- [ ] **4.3 — default behaviour + overridable handlers**
  - Corner drag: move corner `i` to `event.world_position` (opposite corner
    fixed), recompute `center`/`size` (axis-aligned), `update()` the body,
    reposition handles, `flush()`, return `True`.
  - Translation drag: `center += event.world_delta`, `update()`, reposition
    handles, `flush()`.
  - Handlers: `handler` (translate), `on_corner_drag(i, event, rect) -> bool`,
    `on_change(rect)` after any mutation; each returns `True` to fully handle.

- [ ] **4.4 — export + tests**
  - Export `ActRectangle2D`.  Test: entity model, `interaction_config` (body
    disabled), handle spawn count, corner-resize recomputes center/size, and
    translation moves center (using a fake `VizSceneHandle` like `test_active.py`).

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py -q && uv run ruff check py/pytanga/viz/_active.py py/tests/viz/test_act_rectangle2d.py`

## Notes

- Composite by construction: the frontend raycasts one mesh per entity, so each
  grabbable part is its own `ActPoint` entity.  The `ActSceneObject` 1-entity
  contract is unchanged — `ActRectangle2D` composes it.
- Import `ActPoint`/styles lazily where needed to avoid circular imports.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.

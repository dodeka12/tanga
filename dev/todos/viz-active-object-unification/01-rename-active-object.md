# Phase 1 — Rename `_ActWithHandles` → `ActiveObject`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> This is a mechanical rename; the documented "composite" recipe is unchanged.

## Goal

Rename the private base class `_ActWithHandles` to the public `ActiveObject`
and export it, so callers can `isinstance(act, ActiveObject)` without touching a
private name.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (the `_ActWithHandles`
  reference in the "Composite handle controls" section)

## Steps

- [x] **1.1 — Rename the class.**
  - In `_active.py`, change `class _ActWithHandles(ActSceneObject):` →
    `class ActiveObject(ActSceneObject):` and update the class docstring's
    "Base for composite actives…" wording.
  - Update the five composite subclasses: `ActRectangle2D(ActiveObject)`,
    `ActEllipse`, `ActCircle`, `ActPolygon`, `ActLine`.
  - Update the `ActSceneObject.remove` docstring reference (`:class:`_ActWithHandles``
    → `:class:`ActiveObject``).
- [x] **1.2 — Export `ActiveObject`.**
  - Add `ActiveObject` to the `_active` import block and to `__all__` in
    `py/pytanga/viz/__init__.py`.
- [x] **1.3 — Update the architecture doc.**
  - In `docs/dev/architecture/viz-controls-and-interactions.md`, replace
    `` `_ActWithHandles` `` with `` `ActiveObject` ``.
- [x] **1.4 — Verify no stale references.**
  - `grep -rn _ActWithHandles py/ docs/dev/` returns nothing.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check . && uv run ty check`

## Notes

- Keep `_ActWithHandles` as a deprecated alias only if needed; otherwise remove it
  outright (nothing external should reference it).

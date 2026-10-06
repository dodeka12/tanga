# Phase 4 — `ActPolygon`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If this
> work introduces or changes architecture, update the developer docs.

## Goal

Add `ActPolygon`, an editable open/closed `PointPath` with per-vertex `ActPoint`
handles and a translate handle.  Start/end vertices can be **extended** by
Ctrl+dragging them (inserts a new endpoint) and **trimmed** by Ctrl+right-clicking
them (deletes the endpoint).

## Files

- Edit: `py/pytanga/viz/_active.py` (new `ActPolygon`)
- Edit: `py/pytanga/viz/__init__.py` (export `ActPolygon`)
- New: `py/tests/viz/test_act_polygon.py`

## Steps

- [x] **4.1 — Model.**
  - `ActPolygon(points, *, closed=True, show_translate_handle=True,
    handle_style=None, act_style=None, on_vertex_drag=None, on_translate=None,
    on_change=None, on_click=None)`; inherit `_ActWithHandles`.
  - Hold `_points: list[Point]`; `entity` returns a `PointPath` built from
    `_points` (append the first point at the end when `closed=True`).
- [x] **4.2 — Handles.**
  - Spawn one `ActPoint` per vertex and a translate handle at the centroid.
    Vertex handles use `handle_style` and a `handler` closure capturing the index.
- [x] **4.3 — Vertex move handler (modifier branch).**
  - In the closure, if the index is start (0) or end (-1) **and**
    `ModifierKey.CTRL in event.modifiers`, treat as insert (4.4); otherwise move
    `_points[index]` to `event.world_position`.  Always rebuild body, refresh
    handles, flush, fire `on_change(list[Point])`, return `True`.
- [x] **4.4 — Ctrl+drag insert (start/end).**
  - Start + Ctrl: insert `event.world_position` at index 0 (new start).  End +
    Ctrl: append it (new end).  Rebuild/refresh/flush/`on_change`.
- [x] **4.5 — Ctrl+right-click delete (start/end).**
  - Give the start/end vertex handles
    `click_bindings=[ClickBinding(MouseButton.RIGHT, delete_handler,
    ModifierKey.CTRL)]` (requires phase 1).  On match, remove that vertex;
    guard against dropping below two vertices.  Rebuild/refresh/flush/`on_change`.
- [x] **4.6 — Export + tests.**
  - Export `ActPolygon`; add `test_act_polygon.py` covering entity closure,
    vertex move, Ctrl+drag insert at both ends, Ctrl+right-click delete at both
    ends, minimum-vertex guard, `on_change`, `remove()`.

## Validation

```
uv run pytest py/tests/viz/test_act_polygon.py py/tests/viz/test_act_rectangle2d.py -q
```

## Notes

- Interior vertices ignore Ctrl insert/delete (they only move), per request.
- `PointPath` is an open polyline; closure is the composite's responsibility.
- Use `Direction`/`Point` from `pytanga.geometry`; keep the body z = 0 for 2D.

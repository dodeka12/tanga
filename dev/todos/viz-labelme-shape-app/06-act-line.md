# Phase 6 — `ActLine` (single-`Line` composite)

## Goal

Add a dedicated `ActLine` composite that wraps a single `Line` entity
(`Line.from_points(start, end)`) — two endpoint handles + a translate handle,
body `on_click` for selection.  No vertex insert/delete (a line is exactly two
points).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  Reuses `_ActWithHandles` and the existing `Line`
> entity (`line.js` + `LineStyle`); no architecture change.

## Files

- Edit: `py/pytanga/viz/_active.py` (`ActLine`; import `Line`)
- Edit: `py/pytanga/viz/__init__.py` (export `ActLine`)
- New: `py/tests/viz/test_act_line.py`

## Steps

- [x] **6.1 — `ActLine(_ActWithHandles)` class**
  - Constructor takes `start`/`end` points, `show_translate_handle`,
    `handle_style`, `translate_handle_style`, `act_style`, `on_endpoint_drag`,
    `on_translate`, `on_change`, `on_click`.
  - `entity`/`line` property returns `Line.from_points(start, end)`; body
    `on_click` mirrors `ActEllipse`.
- [x] **6.2 — Handles**
  - Spawn two endpoint handles (`handle_style`) at `line.start`/`line.end`, and a
    midpoint translate handle (`translate_handle_style`); no rotate/vertex
    insert/delete.
- [x] **6.3 — Endpoint drag + translate**
  - `_dispatch_endpoint_drag(i, event)`: move that endpoint, rebuild the `Line`
    (keep the other endpoint anchored), commit.  `_translate_by(delta)` moves
    both endpoints by `delta`.
- [x] **6.4 — `create_from_points(a, b)`**
  - Classmethod returning `ActLine(start=a, end=b, …)`.
- [x] **6.5 — Export + tests**
  - Export `ActLine`; test `entity` is a `Line` with the right endpoints,
    endpoint drag, translate, and `create_from_points`.

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- No new renderer — the body is a `Line` (`line.js`, `LineStyle`).
- A line is always open and has exactly two points; labelme `line` maps here,
  while `linestrip` (N points) maps to an open `ActPolygon` (Phase 5).

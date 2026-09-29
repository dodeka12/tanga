# Phase 5 — `ActPolygon` generalized vertex editing

## Goal

Generalize `ActPolygon` so Ctrl+drag **any** vertex inserts a new vertex after it,
and right-click deletes a vertex: Ctrl+right-click preserves the open/closed
state (a closed polygon stays closed while ≥3 vertices remain), and
Ctrl+Shift+right-click also opens a closed polygon.  Replaces the current
endpoint-only behavior.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This extends the existing `ActPolygon` interaction;
> no architecture change.

## Files

- Edit: `py/pytanga/viz/_active.py` (`ActPolygon`)
- Edit: `py/tests/viz/test_act_polygon.py`

## Steps

- [x] **5.1 — `_insert_after(index, pos)`**
  - Generalize `_insert_endpoint` to insert **after** `index` for any index
    (`points.insert(index + 1, p)`), keeping the deferred-handle-rebuild /
    `_insert_drag_index` continuation so the in-flight drag isn't cancelled.
- [x] **5.2 — Insert on any vertex (Ctrl+drag)**
  - In `_dispatch_vertex_drag`, drop the `_is_endpoint(index)` guard: a Ctrl+drag
    on any vertex starts an insert after it (one per drag); a plain drag still
    moves the vertex.
- [x] **5.3 — Delete on any vertex (Ctrl+right-click)**
  - `_make_delete_bindings(i)` returns a Ctrl+right-click `ClickBinding` for
    **every** vertex (remove the `_is_endpoint` early return).
  - `_delete_vertex(i)`: if `len(points) <= 2` → remove the whole composite
    (call `self.remove()` and notify the owner via `on_removed`/`on_change`);
    else `pop(i)`, keep `_closed` unchanged — but if the polygon was closed and
    fewer than 3 vertices remain, set `_closed=False` (a closed polygon needs
    ≥3 vertices).
- [x] **5.4 — Delete + open (Ctrl+Shift+right-click)**
  - Add a second `ClickBinding` with modifiers `{CTRL, SHIFT}`; on click, delete
    the vertex and force `_closed=False` (a closed polygon opens; an open
    polygon is a plain delete).
  - When re-opening a closed polygon, restore `auto_close` so the endpoints can
    be re-fused.
- [x] **5.5 — Keep auto-close on endpoints only**
  - `_is_endpoint`/`_maybe_auto_close` still apply only to start/end (unchanged);
    mid-vertex Ctrl+drag never triggers auto-close.
- [x] **5.6 — `create_from_points(a, b)`**
  - Classmethod building a **2-vertex open** polygon (`closed=False`,
    `auto_close=True`) from two anchor points.
- [x] **5.7 — Tests**
  - Ctrl+drag a middle vertex inserts after it; Ctrl+right-click a middle vertex
    deletes it while keeping a closed polygon closed (≥3 vertices) and opening a
    3-vertex polygon down to 2; Ctrl+Shift+right-click opens a closed polygon;
    deleting down to one vertex removes the composite; endpoint auto-close still
    works; `create_from_points` returns an open polygon.

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- `ActLine` (Phase 6) wraps a 2-point `Line`, so it does **not** need the
  generalized vertex insert/delete — this phase is `ActPolygon`-only.
- "Whole-polygon delete" needs a signal the example/app can observe; prefer
  reusing `on_change` with an empty list, or add `on_removed: Callable[[], None]`
  if `on_change` proves insufficient.

# Phase 1 — Stable vertex identity, tags, and selection state

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Give `ActPolygon` a stable vertex identity and a per-vertex tag store, and add
the selected-vertex state without changing rendering yet.  Later phases key tag
colors and segment colors by the same IDs.

## Files

- Edit: `py/pytanga/viz/_active.py`
- New: `py/tests/viz/test_act_polygon_tags.py`
- Edit: `py/tests/viz/test_act_polygon.py` (`_FakeHandle` records style updates)

## Steps

- [x] **1.1 — Stable vertex IDs**
  - Add `self._vertex_ids: list[int]` initialized to
    `list(range(len(self._points)))` and a monotonic `self._next_vertex_id`
    counter (never reuse IDs).
  - Add `_vertex_index(vertex_id) -> int` returning `-1` when the ID is gone.
  - Add `vertex_count -> int` (`len(self._points)`) for apps that need the
    current count without copying `points`.
  - Keep `_points` as the geometry source; IDs are bookkeeping only.
  - Update `_insert_after`, `_delete_vertex`, and `_fuse_endpoints` to keep
    `_vertex_ids` exactly parallel to `_points`:
    - insert: insert a fresh ID at the same index;
    - delete: pop the removed ID;
    - fuse: pop the last ID (the start vertex survives as the joint).

- [x] **1.2 — Tag store and default tag**
  - Add constructor kwargs:
    - `vertex_tags: Sequence[str | None] | None = None`
    - `default_vertex_tag: str | None = None`
  - Store `self._vertex_tags: dict[int, str | None]`, keyed by vertex ID.
  - When `vertex_tags is None`, seed every current ID with
    `default_vertex_tag`; otherwise require `len(vertex_tags) == len(points)`
    (`ValueError` on mismatch) and store each entry.
  - Add `vertex_tags -> list[str | None]` returning values in current index
    order.
  - Add `set_vertex_tags(tags)` (exact length, `ValueError` otherwise) and
    `set_vertex_tag(index, tag)` (`IndexError` for a bad index).
  - New vertices inserted/prepended by `_insert_after` get
    `default_vertex_tag`; deleted/fused IDs are removed from the dict.
  - Tags are visual only: do **not** call `_on_change` or `_on_removed`.

- [x] **1.3 — Selected vertex state**
  - Add `self._selected_vertex_id: int | None = None`.
  - Add `selected_vertex -> int | None` (the current index of the selected ID,
    or `None` when it has been removed).
  - Add `set_selected_vertex(index | None)`; validate the index and store the
    corresponding ID.  This phase only stores state; phase 2 adds restyling.
  - When the selected ID is deleted or fused, clear the selection.
  - An insert/prepend before the selected vertex must not clear it: the ID
    survives and the public index shifts automatically.

- [x] **1.4 — Supporting callback setter**
  - Add `set_on_change(handler: Callable[[list[Point]], None] | None)` to
    replace `self._on_change` after construction.  The calibrated app uses it
    to install a per-act refresh closure once `DragPreview.finalize()` returns
    the act.
  - Keep the constructor argument and existing callback behaviour unchanged.

- [x] **1.5 — Tests**
  - Extend `_FakeHandle` in `test_act_polygon.py` with no-op `update` and
    `update_style` methods (recording calls) so later phases can assert style
    changes.
  - `test_act_polygon_tags.py`:
    - default tags are all `None`; `default_vertex_tag="1"` fills every vertex;
    - explicit `vertex_tags` round-trips; wrong length raises `ValueError`;
    - `set_vertex_tag(s)` updates values; out-of-range index raises;
    - Ctrl-insert at the start/middle/end gives the new vertex the default tag
      and leaves existing tags attached to their IDs;
    - delete/fuse removes the tag; deleting the selected vertex clears
      `selected_vertex`; inserting before it keeps the ID selected and shifts
      the index;
    - `set_on_change` replaces the callback (fire `_dispatch_vertex_drag` and
      observe the new callback).

## Validation

`uv run pytest py/tests/viz/test_act_polygon.py py/tests/viz/test_act_polygon_tags.py -q`

## Notes

- Do not change handle styles in this phase; phase 2 owns restyling.
- Do not serialize tags here; labelme persistence is phase 5.
- `_vertex_ids` must stay parallel to `_points` through every structural edit;
  later phases depend on that invariant.

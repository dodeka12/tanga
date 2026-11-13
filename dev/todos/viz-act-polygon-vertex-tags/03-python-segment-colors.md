# Phase 3 — Python segment colors and serialization

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add per-segment color overrides to `PointPath`, expose them on `ActPolygon` with
stable-identity remapping, and serialize them as `segmentColors`.

## Files

- Edit: `py/pytanga/viz/_point_path.py`
- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/pytanga/viz/serializer.py`
- New: `py/tests/viz/test_point_path_colors.py`
- Edit: `py/tests/viz/test_act_polygon_tags.py`
- Edit: `py/tests/viz/test_node_serialization.py`

## Steps

- [x] **3.1 — `PointPath` segment-color storage**
  - Add `self._segment_colors: list[str | None]` in `__post_init__`.
  - Add `segment_colors -> list[str | None]`, padded to
    `max(0, len(self._points) - 1)`.
  - Add `set_segment_colors(colors)`: require exactly the current segment count
    (`ValueError` otherwise); store a copy.
  - Add `set_segment_color(index, color)`: validate `0 <= index <
    segment_count`, extend with `None` gaps as needed.
  - `add` appends a `None` segment color.  When `max_points` pops the oldest
    point, pop the oldest segment color too.  If `remove` exists, shift the
    list there as well.
  - Segment `i` connects point `i` to point `i+1`.

- [x] **3.2 — `ActPolygon` segment colors keyed by vertex ID**
  - Add `self._segment_colors: dict[int, str]` keyed by the **start vertex ID**.
  - Add `segment_count` (`len(points)` when closed and `len(points) > 1`, else
    `max(0, len(points) - 1)`) and `segment_colors -> list[str | None]` in
    segment order.
  - Add `set_segment_colors(colors)`: require exactly `segment_count`
    (`ValueError` otherwise); `None` entries clear the corresponding key.
  - Add `set_segment_color(index, color)` and `clear_segment_color(index)`.
  - `_build_path` calls `path.set_segment_colors(...)` after adding the points
    and the closing point:
    - closed: `[self._segment_colors.get(self._vertex_ids[i]) for i in range(n)]`
    - open: `[self._segment_colors.get(self._vertex_ids[i]) for i in
      range(n - 1)]`
  - Structural edits:
    - `_insert_after` gives the new ID no outgoing segment color; the previous
      vertex keeps its color (now on the segment to the new vertex);
    - `_delete_vertex` pops the removed ID's outgoing color; the previous
      vertex's color now targets the next vertex;
    - `_fuse_endpoints` pops the removed endpoint's color; the closing segment
      uses the surviving last vertex's entry.
  - `set_segment_color(s)` calls `self.update()` + `self.flush()` but **not**
    `_on_change` (segment color is visual only).

- [x] **3.3 — Serializer**
  - In `_serialize_point_path`, add `"segmentColors"` only when
    `any(c is not None for c in ent.segment_colors)`.
  - Emit the full list with `null` for unset segments (camelCase key).
  - Leave `points` and `colors` unchanged.

- [x] **3.4 — Tests**
  - `test_point_path_colors.py`:
    - set/pad/invalid length; `set_segment_color` validates the index;
    - `add` appends `None`; `max_points` popping shifts colors;
    - serializer omits `segmentColors` when empty/all-`None` and emits the list
      when any entry is set;
    - explicit segment colors override per-point colors in later phase-4
      renderer tests (here only assert the Python data).
  - `test_act_polygon_tags.py`:
    - closed polygon has `n` segments including `v_{n-1} → v_0`; open has
      `n-1`;
    - `set_segment_colors` round-trips and rejects a wrong length;
    - insert/prepend/delete/fuse remap start-vertex-keyed colors as specified;
    - segment-color changes do not fire `on_change`.
  - `test_node_serialization.py`: a `PointPath` with segment colors serializes
    `segmentColors`; a plain path does not contain the key.

## Validation

`uv run pytest py/tests/viz/test_point_path_colors.py py/tests/viz/test_act_polygon_tags.py py/tests/viz/test_node_serialization.py -q`

## Notes

- Segment colors are CSS hex strings; do not validate color syntax.
- `PointPath.add` gets no new keyword; `ActPolygon` assigns colors after
  building the path.
- A closed `ActPolygon` body appends the first point once; the resulting
  `PointPath` then has exactly `n` segments, matching `ActPolygon.segment_count`.

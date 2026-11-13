# ActPolygon vertex tags & segment colors — Overview

**Created:** 2026-11-13 | **Status:** In progress | **Branch:** `viz-act-polygon-vertex-tags`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Extend `ActPolygon` with per-vertex string tags and a tag→color mapping, a
programmatically settable selected vertex with a custom marker style, and
per-segment color overrides keyed by stable vertex identity.  Add `PointPath`
segment colors and frontend rendering, round-trip tags and segment colors
through labelme JSON, demonstrate the API in `image_labeling_app.py`, and add a
keyboard-driven tagged-labeling workflow to `calibrated_labeling_app.py`
(select a vertex, press `1`/`2`, default tag `1`, tag `2` magenta, magenta
segment ranges computed on the backend).

## Architecture (short)

- `py/pytanga/viz/_active.py` — `ActPolygon` gains stable `_vertex_ids`; tags,
  selection, and segment colors are keyed by ID; public API exposes indices.
  `TAG_PALETTE` + deterministic tag color.  Handle restyling applies the
  documented precedence.
- `py/pytanga/viz/_point_path.py` — `PointPath.segment_colors` /
  `set_segment_color(s)`; explicit segment colors override per-point colors.
- `py/pytanga/viz/serializer.py` — emits `segmentColors` only when any entry is
  non-`None`.
- `py/pytanga/viz/templates/renderers/path-colors.js` (new) +
  `point_path.js` + `utils.js` + `views/three-view.js` — colored-path
  detection, segment-color flattening, and in-place base-color updates without
  tinting explicit vertex colors.
- `py/pytanga/viz/labelme.py` — `LabelShape.vertex_tags` /
  `segment_colors`, `LabelMeLoadResult.warnings`, `iter_shapes`, 3-tuple
  `shapes_from_objects`.
- Examples — `image_labeling_app.py` gains tagging controls and save/load;
  `calibrated_labeling_app.py` gains backend key handlers and the magenta
  range helper.
- Docs + changelog last.

**Developer docs to check:** `docs/dev/architecture/viz-architecture.md`
(scene/layout model, renderer extension recipe, `_RENDERER_FILES`,
`build-viewer-js.py`) and
`docs/dev/architecture/viz-controls-and-interactions.md` (the one `(id, event)`
registry, `ControlView` contract, and the `on_key`/interaction handler path).

### Fixed contract

**Stable vertex identity.** `ActPolygon` keeps a monotonic `_vertex_ids` list
parallel to `_points`.  Tags, the selected vertex, and segment colors are
stored by vertex ID; public properties/setters use indices and remap
automatically on insert/prepend/delete/fuse.  Removing or fusing the selected
vertex clears the selection.

**Tags.** `vertex_tags -> list[str | None]`, `set_vertex_tag(index, tag)`,
`set_vertex_tags(tags)`, `default_vertex_tag: str | None = None` constructor
kwarg.  Tags are arbitrary strings; `None` means untagged.  `tagging: bool =
False` constructor/setter.  `set_tag_color(tag, color)`; fallback
`TAG_PALETTE[zlib.crc32(tag.encode()) % len(TAG_PALETTE)]`.  Tag changes are
visual only (no `on_change`).

**Selected vertex.** `selected_vertex -> int | None`,
`set_selected_vertex(index | None)`, `selected_handle_style: PointStyle | None`
(default `#ffff44`, otherwise a copy of the base handle style),
`select_on_click: bool = True`, `on_vertex_click(index, event, act)`.
Clicking a vertex selects it (when enabled), fires `on_vertex_click`, then the
body's `on_click`.  Selection is visual only (no `on_change`).

**Handle precedence.** Base = `end_handle_style` for an open endpoint when
`tagging=False`, else `handle_style`; if `tagging=True` and the vertex has a
tag, base = that tag's color; if selected, base = `selected_handle_style`.
The selected style always wins.  Tag colors only show in tagging mode.  The
translate handle is unchanged.

**Segment colors.** Segment `i` = `v_i → v_{i+1}`; for a closed polygon
segment `n-1` = `v_{n-1} → v_0`; the color is attached to the **start** vertex
ID.  `ActPolygon.vertex_count` = `len(points)`; `segment_count` = `n` when
closed and `n > 1`, else `max(0, n - 1)`.  `segment_colors -> list[str | None]`,
`set_segment_colors(colors)` (exact
length, else `ValueError`), `set_segment_color(index, color)`,
`clear_segment_color(index)`.  Structural edits keep start-vertex-keyed colors:
insert/prepend gives the new vertex no outgoing color; delete/fuse drops the
removed vertex's outgoing color.  Segment-color changes are visual only (no
`on_change`).  Add `set_on_change(handler)` so the calibrated app can install a
per-act refresh closure after construction.

**PointPath.** `segment_colors -> list[str | None]` (length
`max(0, len(points) - 1)`), `set_segment_colors(colors)`,
`set_segment_color(index, color)`.  Explicit segment colors override both
endpoints' per-point colors; `None` falls back to per-point colors.  `add`
appends a `None` segment; `max_points` popping shifts segment colors.
Serialized as `segmentColors` only when any entry is non-`None`.

**Wire.** `PointPath` JSON gains `segmentColors: (string|null)[]` only when
non-empty.  `path-colors.js` exports `hasExplicitPathColors(ent)` and
`pathColorChangeNeedsColorUpdate(ent, prev)`.  `point_path.js` flattens
per-segment colors first, then per-point colors, then the uniform fallback.
`utils.js` skips `material.color` writes for `vertexColors: true`;
`views/three-view.js` routes a colored path's style-color change through
`updateEntityMesh`/`updatePointPath`.

**LabelMe.** `LabelShape.vertex_tags: list[str | None] | None` and
`segment_colors: list[str | None] | None`; custom shape keys `vertex_tags` and
`segment_colors`, omitted when empty/all-`None`.  `vertex_tags` align to
canonical vertices (closing duplicate dropped).  `segment_colors` length = `n`
closed / `n-1` linestrip.  `LabelMeLoadResult.warnings: list[str]`; malformed
metadata warns and is ignored while the shape still loads.  `iter_shapes(doc)
-> ([(entity, LabelShape)], errors)`; `iter_objects` delegates.
`shapes_from_objects` accepts 2- or 3-tuples (3rd = `vertex_tags`) and reads
`segment_colors` from `PointPath`.

**Calibrated app.** Every polygon vertex defaults to tag `"1"`; tag `"1"` uses
the red handle color, tag `"2"` uses `#ff00ff`.  `world.on_key("1"|"2", ...)`
handlers read `labeler.selected` + `act.selected_vertex`, set the tag, recompute
segment colors from the tags, and clear the selected vertex so the tag color is
visible (the polygon stays selected).  Segment ranges are computed **on the
backend** by `_tag_two_segment_colors(tags, *, closed, color="#ff00ff")`: scan
vertices in index order from `v0`; each vertex's tag labels its **outgoing**
segment (the segment from that vertex to the next vertex in polygon order; for
a closed polygon the last vertex labels the closing segment back to the first).
A `"1"` (or any non-`"2"`) tag leaves the segment at the default color; a `"2"`
tag colors it magenta.  Multiple separate `"2"` vertices therefore produce
multiple separate magenta segments.

## Decisions (confirmed)

- Persist both `vertex_tags` and `segment_colors` in labelme JSON as custom
  shape keys (matches the stated goal).
- Per-segment colors are keyed by stable vertex identity, not raw indices.
- Tag colors are deterministic via `TAG_PALETTE`; explicit `set_tag_color`
  wins.
- Selected style always wins over tag color; the calibrated app clears the
  vertex selection after tagging so the tag color is visible.
- Magenta segments use the "each vertex labels its outgoing segment" scan from
  `v0` described above; the last vertex of a closed polygon labels the closing
  segment.
- No new frontend interaction/event type; selection is backend state and clicks
  use the existing `on_click` path.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-stable-vertex-identity-and-tags.md](./01-stable-vertex-identity-and-tags.md) | Stable vertex IDs, tags, default tag, selection state, supporting setters |
| 2 | [02-tagging-mode-and-selection.md](./02-tagging-mode-and-selection.md) | Tag palette, tagging mode, selected handle style, click selection, restyling |
| 3 | [03-python-segment-colors.md](./03-python-segment-colors.md) | `PointPath` + `ActPolygon` segment colors and serializer |
| 4 | [04-frontend-colored-path.md](./04-frontend-colored-path.md) | `path-colors.js`, `point_path.js`, `utils.js`, `three-view.js`, bundle rebuild |
| 5 | [05-labelme-roundtrip.md](./05-labelme-roundtrip.md) | `vertex_tags`/`segment_colors` JSON, warnings, `iter_shapes`, tests |
| 6 | [06-image-labeling-app.md](./06-image-labeling-app.md) | Tagging controls + save/load in `image_labeling_app.py` |
| 7 | [07-calibrated-labeling-app.md](./07-calibrated-labeling-app.md) | Key 1/2 tagged labeling, default 1, magenta tag 2 + segment ranges |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Docs, generated example docs, changelog, full validation |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_act_polygon.py
  py/tests/viz/test_act_polygon_tags.py -q`; `uv run pytest
  py/tests/viz/test_point_path_colors.py py/tests/viz/test_node_serialization.py
  -q`; `uv run pytest py/tests/viz/test_labelme.py -q`; `uv run pytest
  py/tests/viz/test_app.py py/tests/viz/test_calibrated_labeling_example.py -q`.
- JS: `npm --prefix js/dev test`; `npm --prefix js/dev run check`; `uv run
  pytest py/tests/viz/test_export_renderers.py -q`.
- Bundle: `uv run python tools/build-viewer-js.py` then `uv run python
  tools/build-viewer-js.py --check`.
- Docs: `uv run python tools/generate-example-docs.py` then `--check`; `uv run
  mkdocs build --strict`.
- Full gate: `uv run pytest -q`, `uv run ruff check .`, `uv run ty check`,
  `npm --prefix js/dev test`, `npm --prefix js/dev run check`.

## Non-goals

- Multi-vertex selection.
- Persisting the selected vertex in labelme.
- A new selection event type or frontend selection state.
- Validating a tag vocabulary (any string is allowed).
- A new frontend interaction/event wiring path.
- Editing the image/calibrated app's existing file formats beyond the two
  custom shape keys.

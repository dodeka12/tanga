# Phase 7 — Calibrated labeling app: key-driven tagged labeling

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add the requested tagged-labeling workflow to
`py/examples/apps/calibrated_labeling_app.py`: click a polygon vertex, press
`1` or `2` to tag it, default every vertex to `1`, render tag `2` magenta, and
draw all segments in a `2`-tagged range magenta — all decided by the backend
key handler.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/tests/viz/test_calibrated_labeling_example.py`

## Steps

- [x] **7.1 — Tag configuration**
  - Add module constants:
    - `_TAG_DEFAULT = "1"`
    - `_TAG_MAGENTA = "2"`
    - `_TAG_ONE_COLOR = "#ff4444"` (the existing red vertex handle)
    - `_TAG_TWO_COLOR = "#ff00ff"` (magenta)
  - In `_CalibratedLabeler.__init__`, register the backend keys:
    `world.on_key("1", self._on_tag_one)` and
    `world.on_key("2", self._on_tag_two)`.
  - Add `_configure_polygon(act)`:
    - `act.set_tagging(True)`;
    - `act.set_tag_color("1", _TAG_ONE_COLOR)`;
    - `act.set_tag_color("2", _TAG_TWO_COLOR)`;
    - ensure every `None` tag becomes `"1"` (or rely on
      `default_vertex_tag="1"`);
    - if `act.segment_colors` has no non-`None` entry, set it to
      `_tag_two_segment_colors(act.vertex_tags, closed=act.closed)` so newly
      created and tag-only-loaded polygons show the derived ranges.
  - Pass `default_vertex_tag="1"` to the polygon `DragPreview`
    `factory_kwargs` and to the `ActPolygon` created in `_act_from_entity`.
  - Call `_configure_polygon` from `_add_shape` for every `ActPolygon`, after
    `self._world.add(act, style=style)` (so the handles exist) and after
    applying any loaded tags/colors.  Fill any remaining `None` tags with
    `"1"` there as a safety net.

- [x] **7.2 — Magenta range helper (pure, backend)**
  - Add module-level
    `_tag_two_segment_colors(tags: list[str | None], *, closed: bool, color:
    str = _TAG_TWO_COLOR) -> list[str | None]`:
    - `n = len(tags)`; `seg_count = n if closed and n > 1 else max(0, n - 1)`;
    - `colors = [None] * seg_count`;
    - for `i in range(seg_count)`: if `tags[i] == "2"`, set `colors[i] = color`;
    - return `colors`.
  - Document the rule in the docstring: a vertex's tag labels its **outgoing**
    segment (the segment to the next vertex in polygon order; the last vertex of
    a closed polygon labels the closing segment).  `"1"` → default, `"2"` →
    magenta, so separate `"2"` vertices give separate magenta segments.
  - Add docstring examples (e.g. `["1", "2", "1", "2"]` → segments 1,3 magenta).

- [x] **7.3 — Key handlers**
  - Add (import `KeyEvent` from `pytanga.viz`, or type the parameter as `Any`):
    - `async def _on_tag_one(self, _event: KeyEvent) -> None` →
      `await self._tag_selected(_TAG_DEFAULT)`
    - `async def _on_tag_two(self, _event: KeyEvent) -> None` →
      `await self._tag_selected(_TAG_MAGENTA)`
  - `_tag_selected(tag)`:
    1. `act = self.selected`; return unless `isinstance(act, ActPolygon)`;
    2. `index = act.selected_vertex`; return if `None`;
    3. `act.set_vertex_tag(index, tag)`;
    4. `act.set_segment_colors(_tag_two_segment_colors(act.vertex_tags,
       closed=act.closed))`;
    5. keep the vertex selected (do **not** clear it) so it can be re-tagged
       without clicking again; the selected style still wins over the tag
       colour while selected;
    6. `self._world.flush()`.
  - Pressing `1` on a `2`-tagged vertex reverts it to red and recomputes the
    magenta ranges.

- [x] **7.4 — Selection integration**
  - `_deselect` calls `self.selected.set_selected_vertex(None)` for an
    `ActPolygon` before clearing `self.selected`.
  - `_select` keeps the existing body selection; the new `ActPolygon` vertex
    click handler selects the vertex, then the body select handler selects the
    shape.
  - Add a short `LabelView` hint to the left pane overlay:
    "Click a vertex, then press 1 or 2 to tag it."
  - When a new polygon is finalized in `_on_drag_end`, call
    `_configure_polygon(act)` and set its segment colors from its tags before
    selecting it.

- [x] **7.5 — Load integration**
  - Change the main loop from `store.iter_objects(...)` to
    `store.iter_shapes(...)`; pass each `LabelShape` to
    `labeler.add_loaded_shape(entity, shape)`.
  - Print `result.warnings` alongside `result.errors` in `main()`.
  - `add_loaded_shape(entity, shape=None)`:
    - create the act;
    - for an `ActPolygon`, apply `shape.vertex_tags` when present, and
      `shape.segment_colors` when present; `_configure_polygon` derives the
      colors from the tags when no explicit segment colors were loaded;
    - call `_add_shape`.
  - The bundled `labels.json` has no tags, so every loaded polygon defaults to
    all-`"1"` and has no magenta segments.

- [x] **7.6 — Tests**
  - Extend `_make_labeler` to expose the `Visualizer` (or add a small helper)
    so the key registration can be asserted:
    `viz._layout.scene("world").config.keyboard` contains `"1"` and `"2"`.
  - `_tag_two_segment_colors` table:
    - all `1` → all `None`;
    - `["1", "2", "1", "1"]` closed → segment 1 magenta;
    - `["1", "2", "1", "2"]` closed → segments 1,3 magenta;
    - `["1", "2", "2", "1"]` closed → segments 1,2 magenta;
    - `["2", "1", "2", "1"]` closed → segments 0,2 magenta;
    - `["1", "1", "1", "2"]` closed → segment 3 (closing) magenta;
    - all `2` closed → every segment magenta;
    - open path `["1", "2", "1"]` → segment 1 magenta.
  - Key handler test: add a polygon, tag vertex 1 (`2`), then vertex 2 (`2`);
    assert each tagged vertex's outgoing segment is magenta, then press `1` on
    vertex 2 and assert only its outgoing segment reverts.
  - Default test: `_add_shape(ActPolygon(...))` → all tags `"1"`, `tagging is
    True`, tag colors set, no magenta segments.
  - Load test: a `LabelShape` with `vertex_tags`/`segment_colors` passed to
    `add_loaded_shape` is applied to the act.

- [ ] **7.7 — Manual smoke (browser, not CI)**
  - `uv run python py/examples/apps/calibrated_labeling_app.py`
  - Draw a polygon, switch to polygon mode, click a vertex, press `2`; the
    vertex and its outgoing segments turn magenta.  Press `2` on a later vertex
    to close the range.  Press `1` on a magenta vertex to revert it.
  - Deferred: requires an interactive browser session (not available in the
    headless implementation environment).

## Validation

`uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/apps/calibrated_labeling_app.py && uv run python tools/generate-example-docs.py --check`

## Notes

- The range decision is backend-only; no frontend color rule is added.
- The selected style always wins over the tag colour, so a selected vertex shows
  the selection marker; it stays selected after tagging so it can be re-tagged.
- A `2`-tagged vertex colors its outgoing segment only; independent `2` vertices
  therefore produce independent magenta segments.
- `world.on_key` lowercases keys, but `"1"`/`"2"` are unaffected.

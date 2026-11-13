# Phase 6 — Tagging controls in the image-labeling example

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Demonstrate the full tag and segment-color API in `image_labeling_app.py`:
toggle tagging mode, edit the selected vertex's tag, pick/clear a segment
color, re-sync the controls on selection, and round-trip both through labelme
save/load.

## Files

- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `py/tests/viz/test_app.py`

## Steps

- [x] **6.1 — Toolbar controls**
  - Add a `CheckboxView("tagging", label="Tagging", value=False, ...)` to the
    toolbar.  On change, store `self.tagging` and call `set_tagging(value)` on
    every `ActPolygon`.
  - Add a tag editor (`ValueEditView`/`TextInputView`) for the selected
    vertex's tag; on change, call `act.set_vertex_tag(index, value or None)`.
  - Add a `ColorPickerView` for the selected segment's color; on change, call
    `act.set_segment_color(index, color)`.
  - Add a `ButtonView` "Clear segment color" calling
    `act.clear_segment_color(index)`.
  - Keep the controls disabled when no polygon vertex/segment is selected.

- [x] **6.2 — Selection and panel re-sync**
  - In `_select`/`_deselect`, clear the previous polygon's
    `set_selected_vertex(None)` and refresh the tag/color controls from the new
    selection.
  - Wire `ActPolygon.on_vertex_click` so clicking a vertex updates the panel
    with that vertex's tag and its outgoing segment color.
  - Guard programmatic control updates with a `self._syncing` flag (or use the
    control's silent setter) so panel re-sync does not re-fire the handlers.
  - The body click still selects the shape; the vertex click selects the
    vertex and then the shape.

- [x] **6.3 — Creation, load, and save**
  - For polygons created by `DragPreview`/`_act_from_entity`, use
    `default_vertex_tag="1"` and apply the current tagging mode in
    `add_shape`.
  - Extend `add_shape(act, label=None, *, vertex_tags=None,
    segment_colors=None)`; for an `ActPolygon`, apply the provided tags/colors
    after construction.
  - `load_document`: use `self._store.iter_shapes(doc)` and pass each
    `LabelShape.vertex_tags` / `segment_colors` into `add_shape`; print
    `result.warnings` alongside `result.errors` in `load`.
  - `to_document`: pass 3-tuples for polygons:
    `(s.act.entity, s.label, s.act.vertex_tags)`; `shapes_from_objects` reads
    the segment colors from the `PointPath`.
  - Preserve the existing non-polygon behaviour.

- [x] **6.4 — Tests**
  - Tagging checkbox toggles `ActPolygon.tagging` on all polygons.
  - Tag editor updates the selected vertex's tag; color picker sets the
    selected segment's color; clear resets it.
  - Selection re-syncs the panel values without firing handlers.
  - `to_document` emits `vertex_tags` and `segment_colors`; `load_document`
    restores them onto the acts.
  - Existing `test_app.py` tests still pass.

- [x] **6.5 — Example docstring**
  - Update the module description and `Keywords:` header to mention vertex
    tagging and per-segment colors (see `dev/workflows/example-docs.md`).

## Validation

`uv run pytest py/tests/viz/test_app.py -q && uv run ruff check py/examples/apps/image_labeling_app.py`

## Notes

- Keep panel re-sync one-way: selection → controls; user edits → model.
- The image app does not derive segment colors from tags; the user picks them
  explicitly.  The calibrated app owns the tag→magenta range rule.
- Do not add a new interaction event type; use `on_vertex_click`.

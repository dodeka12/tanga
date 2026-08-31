# Phase 5 — `ControlView` embeds a `Control` (single control model)

## Goal

Remove the duplicated `Control`/`ControlView` hierarchies and value-coercion
helpers so there is one control model and one serializer, while keeping the
`view_layout` wire shape identical.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_layout_api.py`, `py/tests/viz/test_file_chooser.py`

## Steps

- [x] **5.1 — `ControlView` wraps a `Control`**
  - Give `ControlView` a `.control` attribute (an instance of the matching
    `_controls.Control`); `id`/`value`/`label` delegate to it. Keep public
    constructor signatures (`SliderView(cid, …)` etc.) unchanged.

- [x] **5.2 — Single serializer**
  - `ControlView._serialize` emits the layout node type (unchanged) but fills
    fields from `self.control` via `_serialize_one_control`, so panel and layout
    share one field source.

- [x] **5.3 — Drop duplicate value helpers**
  - Remove `set_control_view_value`/`get_control_view_value`; `Visualizer` value
    APIs call `set_control_value`/`get_control_value` on `view.control`.

- [x] **5.4 — Tests**
  - `test_layout_api.py` and `test_file_chooser.py` serialization tests keep
    passing (wire shape unchanged); add a test that panel and layout instances
    of the same kind serialize identical value fields.

## Validation

`uv run pytest py/tests/viz/ -q`

## Notes

- Highest-risk phase: the `view_layout` contract must not change. Compare
  serialized output before/after in the tests (snapshot/round-trip).

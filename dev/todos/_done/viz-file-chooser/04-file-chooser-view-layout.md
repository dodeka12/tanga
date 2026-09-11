# Phase 4 — `FileChooserView` (layout control view)

## Goal

Make the control usable in layouts/panels, like `ButtonView`.

## Steps

- [x] **4.1 — `FileChooserView(ControlView)` (`views.py`)**
  - `_node_type = "file_chooser_view"`; fields `cid`, `label`, `value`,
    `placeholder`, `root`, `accept`, `on_change`; `_serialize` mirrors
    `ButtonView` plus the extra fields.

- [x] **4.2 — `views/file-chooser-view.js`**
  - `FileChooserView extends ControlView`; `render()` returns
    `createFileChooser({ id: controlId, ... })`.

- [x] **4.3 — `build.js`**
  - Map `file_chooser_view` → `FileChooserView`.

- [x] **4.4 — Handler registration**
  - `views.py::iter_control_views` already yields `ControlView` subclasses;
    confirm `FileChooserView.on_change` registers via the existing
    `set_layout` registration path.

## Validation

`uv run pytest py/tests/viz/test_views.py py/tests/viz/test_layout_api.py -q` +
`node --input-type=module --check`.

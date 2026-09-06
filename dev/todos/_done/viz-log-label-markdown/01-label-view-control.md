# Phase 1 — `LabelView` display control

## Goal

Deliver `LabelView` — a non-editable, settable text control (`value` + `font_size`)
that updates live through the existing `control_update` path.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/viz/templates/controls-panel.js`
- New: `py/pytanga/viz/templates/views/label-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- New: `py/pytanga/viz/templates/themes/views/label-view.css`
- Edit: `py/pytanga/viz/templates/themes/registry.json`
- Edit: `py/tests/viz/test_themes.py`, `py/tests/viz/test_views.py`, `py/tests/viz/test_controls.py`

## Steps

- [x] **1.1 — Backend `Label` control (`_controls.py`)**
  - Add `@dataclass class Label(Control)` with `kind: str = "label"`,
    `value: str = ""`, `font_size: float = 14`.
  - Add a `Label` branch to `_serialize_one_control`
    (`{"value": ctrl.value, "font_size": ctrl.font_size}`).
  - Add `Label` to `get_control_value` (return `ctrl.value`) and
    `set_control_value` (`ctrl.value = str(value)`).

- [x] **1.2 — Backend `LabelView` + export**
  - `views.py`: add `LabelView(ControlView)` with `_node_type = "label_view"`,
    constructor `(cid, *, value="", font_size=14, **kwargs)` that calls
    `super().__init__(cid, **kwargs)` then sets
    `self.control = Label(id=cid, value=value, font_size=font_size)`.
  - Add `LabelView` to `views.py __all__`.
  - `__init__.py`: import `LabelView` from `.views` and add to `__all__`
    (do **not** re-export the `Label` control — clash with the 3D `Label`).

- [x] **1.3 — Frontend `createLabel` (`controls-panel.js`)**
  - Add `export function createLabel(ctrl)` that builds a
    `<div class="tanga-control tanga-label">` containing a text element with
    `textContent = ctrl.value` and inline `font-size = ctrl.font_size + 'px'`,
    and registers `_controlRegistry[ctrl.id] = { owner, kind: 'label',
    apply: (v) => { el.textContent = v == null ? '' : String(v); } }`.

- [x] **1.4 — Frontend `LabelView` + `build.js`**
  - New `views/label-view.js`: `LabelView extends ControlView`, constructor
    `{ id, value = '', font_size = 14 }`, `render()` → `createLabel({ id,
    owner: 'layout', value, font_size })`.
  - `build.js`: import `LabelView` and add a `node.type === 'label_view'`
    branch constructing it from `node.id`/`node.value`/`node.font_size`
    (followed by `applySizeSpecs`).

- [x] **1.5 — Theme CSS**
  - New `themes/views/label-view.css` (`.tanga-label` typography + a text class,
    `white-space: pre-wrap`).
  - Add `"views/label-view.css"` to `registry.json` `components` and to
    `test_themes.py::_COMPONENTS`.

- [x] **1.6 — Tests**
  - `test_views.py`: `LabelView` serializes `type == "label_view"`, `value`,
    `font_size`, and the stable control `id`.
  - `test_controls.py`: `get_control_value(Label(…))` and
    `set_control_value(Label(…), 123)` → `"123"` (str coercion).

## Validation

```
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_controls.py py/tests/viz/test_themes.py -q
node --check py/pytanga/viz/templates/controls-panel.js py/pytanga/viz/templates/views/label-view.js py/pytanga/viz/templates/views/build.js
node --test 'dev/src/js-tests/*.test.mjs'
```

## Notes

- Mirror `text-field-view.js` / `createTextField` (string value control) but
  render a read-only text element (no `<input>`, no `sendEvent`).
- Keep the `ControlView` default min-size floors (120×32); users override via
  `min_width`/`min_height` as usual.

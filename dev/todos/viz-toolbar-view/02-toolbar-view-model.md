# Phase 2 — `ToolbarView` backend model

## Goal

Add the `ToolbarView` Python class (`StackView` subclass, `_node_type =
"toolbar"`) with its `margin` / `border` / `gap` / `align` / `justify` surface,
serialization, and public export.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **2.1 — Add `ToolbarView(StackView)` (`views.py`)**
  - `_node_type = "toolbar"`.
  - Constructor `(children, *, margin=Size.px(6), border=True, gap=None,
    align=EStackAlign.CENTER, justify=EStackJustify.START, **kwargs)`.
  - Call `super().__init__("horizontal", children, gap=gap, align=align,
    justify=justify, **kwargs)`; store `self.margin` and `self.border`.
  - Validate `margin` is `None` or a `Size`, and `border` is a `bool`.

- [x] **2.2 — Serialize (`views.py`)**
  - Override `_serialize` to call `super()._serialize(...)` then set
    `result["margin"] = _size_dict(self.margin)` and
    `result["border"] = self.border`.  `direction`/`gap`/`align`/`justify`/
    `children` come from `StackView._serialize`; `type` comes from `_node_type`.

- [x] **2.3 — Export**
  - Add `ToolbarView` to `views.py __all__` and to `py/pytanga/viz/__init__.py`
    (import + `__all__`).

- [x] **2.4 — Tests (`test_views.py`)**
  - `serialize_layout(ToolbarView([ButtonView("b")], gap=4, margin=Size.px(8),
    border=False, justify=EStackJustify.SPACE_EVENLY))["root"]` has
    `type == "toolbar"`, `direction == "horizontal"`, `gap == 4`,
    `margin == {"value": 8.0, "unit": "px"}`, `border is False`,
    `justify == "space-evenly"`, `align == "center"`.
  - Assert `ToolbarView` children serialize in order (one child → one entry).

## Validation

```
uv run pytest py/tests/viz/test_views.py -q
```

## Notes

- `Size` is a frozen dataclass, so `Size.px(6)` is a safe default.
- Keep the constructor keyword-only after `children` (existing convention).

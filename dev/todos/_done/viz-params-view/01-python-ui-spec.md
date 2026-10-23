# Phase 1 — Python `ControlUI` spec model

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (control kinds and the
> `Control` model).  This phase adds pure data (no view, no frontend) and does not
> change architecture.

## Goal

Add the `ControlUI` dataclass hierarchy (one class per control type), the
`param_ui()` helper, and the type→control inference helper.  Pure data, unit-tested
in isolation, with no dependence on the view or server layers.

## Files

- **New** `py/pytanga/viz/_params_ui.py` — `ControlUI` + subclasses, `param_ui()`,
  `_PARAM_UI_KEY`, `infer_control_ui()`.
- **Edit** `py/pytanga/viz/__init__.py` — import + `__all__` entries.
- **New** `py/tests/viz/test_params_ui.py`.

## Steps

- [x] **1.1 — `ControlUI` base + subclasses**
  - Define `@dataclass class ControlUI` with `title`, `tooltip`, `enabled`,
    `skip: bool = False`, and `kind: ClassVar[str] = ""`.
  - Define the subclasses exactly as in the README contract: `SliderUI`
    (`min`/`max`/`step`), `ValueEditUI` (`min`/`max`/`step`/`digits`/`editable`),
    `DropdownUI` (`options`), `CheckboxUI`, `TextFieldUI` (`placeholder`),
    `TextAreaUI` (`placeholder`/`rows`), `ColorPickerUI`, `ButtonUI`
    (`icon`/`icon_only`), `LabelUI` (`font_size`), `MarkdownUI`, `ProgressBarUI`
    (`total`/`indeterminate`/`text`).  Each sets its `kind` class var.
- [x] **1.2 — `param_ui()` helper**
  - `_PARAM_UI_KEY = "param_ui"`.
  - `param_ui(default, *, ui: ControlUI | None = None, **extra_metadata)` returns
    `dataclasses.field(default=default, metadata={...})`, putting `ui` under the
    reserved key and passing `**extra_metadata` through unchanged.
- [x] **1.3 — inference helper**
  - `infer_control_ui(py_type, value) -> ControlUI` per the README table
    (`bool`→`CheckboxUI`, `int`→`ValueEditUI(step=1, digits=0)`,
    `float`→`ValueEditUI`, `str`→`TextFieldUI`/`ColorPickerUI`/`DropdownUI`,
    `list`/`tuple`→`DropdownUI(options=…)`).
  - A small `_ui_kwargs(ui) -> dict` that returns the subclass's non-`None` fields
    (skipping the shared `title`/`tooltip`/`enabled`/`skip`/`kind`) — reused by
    `ParamsView` in Phase 2.
- [x] **1.4 — exports + tests**
  - Export `ControlUI`, each `*UI` subclass, `param_ui`, and `infer_control_ui`
    from `py/pytanga/viz/__init__.py` (import + `__all__`, matching existing style).
  - `test_params_ui.py`: each subclass's `kind` and fields; `param_ui()` writes
    `metadata["param_ui"]` and passes extra keys through; `infer_control_ui()`
    for each type; `_ui_kwargs` omits `None` + shared fields.

## Validation

```bash
uv run pytest py/tests/viz/test_params_ui.py -q
```

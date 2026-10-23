# ParamsView (dict/dataclass → controls) — Overview

**Created:** 2026-10-21 | **Status:** Done | **Branch:** `feat/control-theme`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the "Add a control" recipe and
> "Layout re-push" reconcile notes) and
> `docs/dev/architecture/viz-controls-and-interactions.md` (one `(id, event)`
> registry; every `ControlView` wraps a `Control`).  This work **adds a new view
> type** (`params_view`) following the existing `*View` extension recipe — it does
> not change a documented contract, but the developer docs must be updated in
> Phase 5.

## Goal

Add a `ParamsView` that renders a mapping of values as a two-column, table-like
control: the key/title on the left, a fitting control for the value on the right.
It accepts either a plain `dict` (with an optional `styles` dict) or a
`@dataclass` instance whose fields carry per-field UI metadata.  Every change
fires one `on_change` callback with the full state.

## Architecture (short)

- **Python** — a `ControlUI` dataclass hierarchy (one class per control type) and
  a `param_ui()` helper that writes `dataclasses.field(metadata={"param_ui": ...})`.
  `ParamsView` is a plain `View` whose `children` are ordinary `ControlView`s (one
  per key/field, `cid = f"{view.id}.{key}"`), so `iter_control_views()` registers
  each child's handler on the existing `(id, event)` registry — no new event
  plumbing.
- **Serialization** — a new `params_view` node with `rows = [{key, title, control}]`
  where `control` is a full serialized control-view node carrying `label=""` and
  `hide_label=true`.
- **Frontend** — `build.js` gains a `params_view` branch that recursively builds
  each row's control view; a new `ParamsView` view renders the key cell + control
  cell in a CSS grid; each control factory honors `hide_label`.

## Fixed contract (decided up front — later phases implement against this)

### `ControlUI` hierarchy (`py/pytanga/viz/_params_ui.py`)

```python
@dataclass
class ControlUI:
    title: str | None = None
    tooltip: str | None = None
    enabled: bool | None = None
    skip: bool = False
    kind: ClassVar[str] = ""

@dataclass
class SliderUI(ControlUI):
    kind = "slider"
    min: float | None = None
    max: float | None = None
    step: float | None = None

@dataclass
class ValueEditUI(ControlUI):
    kind = "value_edit"
    min: float | None = None
    max: float | None = None
    step: float | None = None
    digits: int | None = None
    editable: bool | None = None

@dataclass
class DropdownUI(ControlUI):
    kind = "dropdown"
    options: list[str] | None = None

@dataclass
class CheckboxUI(ControlUI):
    kind = "checkbox"

@dataclass
class TextFieldUI(ControlUI):
    kind = "text"
    placeholder: str | None = None

@dataclass
class TextAreaUI(ControlUI):
    kind = "textarea"
    placeholder: str | None = None
    rows: int | None = None

@dataclass
class ColorPickerUI(ControlUI):
    kind = "color"

@dataclass
class ButtonUI(ControlUI):
    kind = "button"
    icon: str | None = None
    icon_only: bool = False

@dataclass
class LabelUI(ControlUI):
    kind = "label"
    font_size: float | None = None

@dataclass
class MarkdownUI(ControlUI):
    kind = "markdown"

@dataclass
class ProgressBarUI(ControlUI):
    kind = "progress"
    total: float | None = None
    indeterminate: bool | None = None
    text: str | None = None
```

`title`/`tooltip`/`enabled`/`skip` are shared; each subclass declares only its own
parameters.  `value` and `on_change`/`on_click` are **not** part of a `*UI` class —
the value comes from the field, the handler is `ParamsView.on_change`.

### `param_ui()` helper

```python
_PARAM_UI_KEY = "param_ui"

def param_ui(default, *, ui: ControlUI | None = None, **extra_metadata):
    meta = dict(extra_metadata)
    if ui is not None:
        meta[_PARAM_UI_KEY] = ui
    return field(default=default, metadata=meta)
```

- The reserved metadata key is the literal `"param_ui"`; any other `metadata` keys
  are the user's own and are ignored by `ParamsView`.
- `param_ui` is sugar over `dataclasses.field(metadata={"param_ui": <ControlUI>})`;
  the raw `field()` form is equivalent and must be shown/documented (Phase 4).
- No string shorthand — `ui` must be a `ControlUI` instance.

### `ParamsView` API

```python
class ParamsView(View):
    _node_type = "params_view"

    def __init__(self, source, styles=None, *, id=None, title="", on_change=None, **view_kwargs):
        ...
```

- `source`: `dict` (values) or a `@dataclass` **instance**.
- `styles`: optional `dict[str, ControlUI]` — a per-key `ControlUI` instance that
  specifies the control type + its parameters (e.g.
  `{"radius": SliderUI(title="Radius", min=0.1, max=5.0)}`).  Layered over
  dataclass field metadata; for dict mode it is the primary UI spec.
- `on_change(state, event)`: `state` is the live `dict` (dict mode) or the
  dataclass instance **mutated in place** (dataclass mode); `event.id` is
  `f"{view.id}.{key}"`.
- `view.values` (dict), `view.instance` (dataclass | None), `view.get_value()`,
  `view.set_value(key, value)`, `view.set_values(mapping)` (pushes per-control
  `control_update` via each child's injected `_push`).

**Type inference** (when a key has no `ControlUI` spec — no `styles[key]`, and no
`"param_ui"` field metadata in dataclass mode):

| value/field type | inferred control |
|---|---|
| `bool` | `CheckboxUI()` |
| `int` | `ValueEditUI(step=1, digits=0)` |
| `float` | `ValueEditUI()` (stepper; use `SliderUI(min,max)` for a range) |
| `str` | `TextFieldUI()` (or `ColorPickerUI` for `#rgb`/`#rrggbb`, `DropdownUI` if `options` given) |
| `list`/`tuple` | `DropdownUI(options=that list, value=first element)` |

### Wire (`params_view` node)

```json
{
  "type": "params_view",
  "id": "v0",
  "title": "",
  "rows": [
    {"key": "radius", "title": "Radius",
     "control": {"type": "slider_view", "id": "v0.radius",
                 "label": "", "hide_label": true, "min": 0.1, "max": 5.0, "step": 0.05, "value": 2.0}},
    {"key": "wireframe", "title": "Wireframe",
     "control": {"type": "checkbox_view", "id": "v0.wireframe",
                 "label": "", "hide_label": true, "value": false}}
  ],
  "min_width": null, "max_width": null, "min_height": null, "max_height": null,
  "preferred_width": null, "preferred_height": null
}
```

`control` is the child `ControlView._serialize()` result; `hide_label` is a new
field on the `Control` base (serialized only when `True`) that makes the control
factory render **without its own label** — the key/title lives in the left column.

## Decisions (confirmed)

- Name `ParamsView`; helper `param_ui()`; reserved metadata key `"param_ui"`.
- Keep the `param_ui()` helper, but also document + example the raw `field()` form.
- `param_ui(default, *, ui=ControlUI | None, **extra_metadata)`; `ui=` keyword
  (not `type=`); no string shorthand.
- `styles` is `dict[str, ControlUI]` — the same `ControlUI` types `param_ui()`
  accepts; no string-key/value style dict.
- Keys/fields with no `ControlUI` spec (no `styles[key]`, no `"param_ui"` metadata)
  infer from the value/field type (table above).
- `on_change(state, event)` delivers the full state; dataclass is mutated in place.
- Label-less rendering via a new `Control.hide_label` flag (Python serialize +
  frontend factories), not a CSS hack (checkbox uses a `<label>` as its row, so a
  blanket CSS `display:none` would hide the whole control).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-ui-spec.md](./01-python-ui-spec.md) | `ControlUI` hierarchy + `param_ui()` + inference + exports + tests |
| 2 | [02-python-params-view.md](./02-python-params-view.md) | `ParamsView` (dict + dataclass) + `Control.hide_label` + serialization + runtime API + tests |
| 3 | [03-frontend-params-view.md](./03-frontend-params-view.md) | `params_view` node + `ParamsView` JS + factories honor `hide_label` + CSS + registry |
| 4 | [04-example.md](./04-example.md) | Example: dict + dataclass (`param_ui`) + raw `field()` alternative |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Architecture doc + user docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `uv run ruff check py/pytanga/viz py/tests/viz` — lint.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests.
- `uv run python tools/build-viewer-js.py` — rebuild the committed viewer bundle after template edits.
- `uv run python tools/generate-example-docs.py --check` — example docs drift (phase 4).
- `uv run mkdocs build --strict` — docs gate (phase 5).

## Non-goals

- No nested dict/dataclass recursion (flat key → control only).
- No string shorthand for `ui` (must be a `ControlUI` instance).
- No new control kind — reuses the existing control factories/views.
- No `FileChooserView` / `TableView` rows (large pane-sized views, not compact controls).
- No auto-derived slider ranges for floats (use `SliderUI(min=…, max=…)`).


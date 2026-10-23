# ParamsView enhancements (adopt it in consumer panels) — Overview

**Created:** 2026-10-21 | **Status:** Done | **Branch:** `feat/paramsview-enhancements`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `Control` model,
> `ControlEvent`, `control_state`/`control_update`, `ControlView`),
> `docs/dev/architecture/viz-architecture.md` (the `ParamsView` extension recipe),
> and `docs/dev/architecture/viz-theme-system.md` (density tokens, group title).
> This work extends the existing `ParamsView` (not a new control kind); the
> `ControlEvent` field addition is anticipated by its docstring.  Update the
> developer docs in Phase 9.

## Goal

Make `ParamsView` able to replace hand-built control panels in consumer apps:
nested dataclasses (rendered as nested `GroupView`s), non-parameter rows
(buttons/status) that can sit above or below the parameters, per-field change
notification + handlers, per-row visible/enabled/title/options at runtime,
correct type coercion (int stays int; `from __future__ import annotations`),
whole-state replacement, and the remaining spec gaps (enums, `(value, label)`,
units, validation, tooltips, theme constructor arg).

## Architecture (short)

`ParamsView` is already a `View` whose `children` are ordinary `ControlView`s
(one per key/field, `cid = f"{view.id}.{key}"`), serialized as a `params_view`
node with `rows`.  The enhancements stay inside that model:

- **Python** — `_params_ui.py` gains fields (`visible`, `on_change`, `coerce`,
  `integer`, `unit`, `(value,label)` options) and a `GroupUI`; `params_view.py`
  gains `extra_rows`/`RowSpec`, nested-group building, row-state methods,
  `set_state`/`add`/`remove`, and annotation-driven coercion.
- **Wire** — `ControlEvent` gains `key`/`value`; row state reuses the existing
  `control_state`/`control_update` messages (keyed by the row's control id).
- **Frontend** — `params-view.js` becomes row-aware (tracks rows by key,
  propagates visible/enabled to the row wrapper, updates title/options); nested
  groups reuse `GroupView` + `params_view` serialization with a `.tanga-group-nested`
  class; the nested title is a new `--tanga-group-nested-title-size` token.

## Fixed contract (decided up front)

### `ControlEvent` (additive)

```python
@dataclass
class ControlEvent:
    browser_id: str | None = None
    key: str | None = None      # NEW — changed field name
    value: Any = None           # NEW — changed value
```

### `ControlUI` (base) — new shared fields

```python
@dataclass
class ControlUI:
    title: str | None = None
    tooltip: str | None = None
    enabled: bool | None = None
    visible: bool | None = None                       # NEW
    skip: bool = False
    on_change: ControlHandler | None = None           # NEW (per-field handler)
    coerce: Callable[[Any], Any] | None = None        # NEW
    kind: ClassVar[str] = ""
```

### `ControlUI` subclasses — changes + one new

```python
@dataclass
class GroupUI(ControlUI):          # NEW — nested dataclass → nested GroupView
    kind: ClassVar[str] = "group"
    collapsed: bool = False

@dataclass
class SliderUI(ControlUI):
    kind = "slider"
    min: float | None = None
    max: float | None = None
    step: float | None = None
    integer: bool = False           # NEW — sugar for coerce=int

@dataclass
class ValueEditUI(ControlUI):
    kind = "value_edit"
    min: float | None = None
    max: float | None = None
    step: float | None = None
    digits: int | None = None
    editable: bool | None = None
    integer: bool = False           # NEW
    unit: str | None = None         # NEW — suffix after the value

@dataclass
class DropdownUI(ControlUI):
    kind = "dropdown"
    options: list[str | tuple[str, str]] | None = None   # NEW — (value, label) pairs
```

### `RowSpec` (non-parameter rows)

```python
@dataclass
class RowSpec:
    key: str
    ui: ControlUI
    value: Any = None
    on_click: ControlHandler | None = None
    on_change: ControlHandler | None = None
    position: Literal["above", "below"] = "below"   # above/below the parameter rows
```

### `ParamsView` API (additions)

```python
class ParamsView(View):
    def __init__(self, source, styles=None, *, id=None, title="",
                 on_change=None, extra_rows: list[RowSpec] | None = None, **view_kwargs): ...

    # row state (acts on the whole row: title + control)
    def set_visible(self, key: str, visible: bool) -> None: ...
    def set_enabled(self, key: str, enabled: bool) -> None: ...
    def set_title(self, key: str, title: str) -> None: ...
    def set_options(self, key: str, options) -> None: ...

    # structure / state (no `on_change` fired)
    def add(self, key: str, value: Any, ui: ControlUI) -> None: ...
    def remove(self, key: str) -> None: ...
    def set_state(self, new_instance_or_dict) -> None: ...   # rebind + update rows
```

- `set_value`/`set_values` are extended to `label`/`markdown`/`progress` display
  rows and documented as **not** firing `on_change`.
- Per-field `on_change` (from `ControlUI.on_change`) is called instead of the
  shared handler when present; the shared `on_change(state, event)` receives
  `event.key`/`event.value`.
- A dataclass-valued field (no `GroupUI`) is auto-detected as a nested group;
  `ui=GroupUI(title=…, collapsed=…)` customizes it.
- Values are coerced to the resolved field type (`typing.get_type_hints`) when no
  `coerce` is set; `Enum`/`Literal` infer a dropdown, `X | None` unwraps to `X`.

## Decisions (confirmed)

- Nested dataclasses render as nested `GroupView`s with a smaller title font
  (`--tanga-group-nested-title-size`), not inline separators.
- Non-parameter rows are declared via `extra_rows=[RowSpec(...)]`; each `RowSpec`
  has `position="above"|"below"` (default below).
- Per-field handlers live on `ControlUI.on_change` (works in both `param_ui` and
  the `styles` dict).
- Coercion is automatic from the resolved annotation, overridable via
  `coerce=` / `integer=True`; `set_state`/`set_value` never fire `on_change`.
- Row state reuses `control_state`/`control_update` (no new wire message).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-change-event-enrichment.md](./01-change-event-enrichment.md) | `ControlEvent.key/value` + per-field `on_change` handlers |
| 2 | [02-type-coercion-inference.md](./02-type-coercion-inference.md) | annotation resolution (string bug) + coercion + Enum/Literal + nullable + `integer=True` |
| 3 | [03-non-parameter-rows.md](./03-non-parameter-rows.md) | `RowSpec` + `extra_rows` + above/below position + display-row `set_value` |
| 4 | [04-row-state.md](./04-row-state.md) | `set_visible`/`set_enabled`/`set_title`/`set_options` + row-aware frontend + `ControlUI.visible` |
| 5 | [05-nested-dataclasses.md](./05-nested-dataclasses.md) | `GroupUI` + nested `GroupView`s + smaller nested title font |
| 6 | [06-state-replacement-mutation.md](./06-state-replacement-mutation.md) | `set_state` (silent) + `add`/`remove` |
| 7 | [07-spec-gaps.md](./07-spec-gaps.md) | dropdown `(value,label)` + units/suffix + `validate` |
| 8 | [08-ergonomics-theme.md](./08-ergonomics-theme.md) | tooltips from docstrings + `Visualizer(theme=…)` + per-View density |
| 9 | [09-docs-changelog.md](./09-docs-changelog.md) | user/developer docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression (extend `test_params_view.py` / `test_params_ui.py`).
- `uv run ruff check py/pytanga/viz py/tests/viz` and `uv run ty check` — lint + type.
- `node js/dev/tests/check-syntax.mjs` + `node --test js/dev/tests/*.test.mjs` — JS gate.
- `uv run python tools/generate-example-docs.py --check` — example docs (phases that touch the example).
- `uv run mkdocs build --strict` — docs gate (phase 9).

## Non-goals

- No new control kind — reuses existing control factories/views.
- No declarative `visible_if` predicates (deferred; the imperative `set_visible` is the first step).
- No collapsible *flat* sections beyond nested `GroupView`s (no `section=` string hints).
- No per-`ParamsView` density flag unless it falls out of the theme work (defer if it needs new plumbing).


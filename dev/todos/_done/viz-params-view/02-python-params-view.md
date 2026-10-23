# Phase 2 — Python `ParamsView` + `Control.hide_label`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (a `ControlView` wraps a
> `Control`; `set_layout` registers child handlers via `iter_control_views`) and
> `docs/dev/architecture/viz-architecture.md` ("Add a control").  `ParamsView` is a
> new view following that recipe; `hide_label` is an additive `Control` field, not
> an architecture change.

## Goal

Add `ParamsView` — a `View` whose children are ordinary `ControlView`s built from a
`dict` or a `@dataclass` instance — plus the `Control.hide_label` flag that lets a
control render label-less inside the params grid.

## Files

- **New** `py/pytanga/viz/views/params_view.py` — `ParamsView`.
- **Edit** `py/pytanga/viz/_controls.py` — add `hide_label: bool = False` to
  `Control` and emit `"hide_label": true` in `serialize()`.
- **Edit** `py/pytanga/viz/views/__init__.py` + `py/pytanga/viz/__init__.py` — export.
- **New** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **2.1 — `Control.hide_label`**
  - Add `hide_label: bool = False` (class-level annotation, like `selected`) to the
    `Control` base; in `Control.serialize()` emit `result["hide_label"] = True`
    when set (mirroring the `enabled`/`visible`/`selected` pattern).
- [x] **2.2 — `ParamsView` construction**
  - `class ParamsView(View)` with `_node_type = "params_view"`.
  - `__init__(self, source, styles=None, *, id=None, title="", on_change=None, **view_kwargs)`:
    - normalize `source` into `self.values` (dict) and, when `source` is a
      `@dataclass`, keep `self.instance = source` and read initial values via
      `getattr`.
    - resolve each key's spec: `styles[key]` (a `ControlUI` instance) or
      `field.metadata["param_ui"]` (dataclass mode), with `styles[key]` layered
      over field metadata when both are present; fall back to
      `infer_control_ui(field.type, value)` when neither is given.
    - build the child `ControlView` (`cid=f"{self.id}.{key}"`, `label=""`,
      kind-specific kwargs from `_ui_kwargs`), set `child.control.hide_label = True`,
      and give it an `on_change` closure that writes `self.values[key] = value`
      (and `setattr(self.instance, key, value)` when applicable) then
      `await self.on_change(state, event)`.
    - store `self.children` (list of `ControlView`), `self.title`, `self.on_change`.
- [x] **2.3 — serialization**
  - `_serialize()` → `type="params_view"`, `id`, `title`, `rows = [{"key", "title",
    "control": child._serialize()}]`, plus the base size fields.
- [x] **2.4 — runtime API**
  - `get_value()` → `dict(self.values)`; `set_value(key, value)` and
    `set_values(mapping)` mutate state and push per-control `control_update` via the
    matching child's `_push`; `values` and `instance` properties.
- [x] **2.5 — exports + tests**
  - Export `ParamsView` from `views/__init__.py` and `pytanga.viz`.
  - `test_params_view.py`: dict-mode and dataclass-mode serialization (`rows`,
    `hide_label`, child ids); inference; `on_change` receives the full dict / the
    mutated instance; `hide_label` serializes only when `True`; `set_value`/`set_values`
    push updates.

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py -q
```

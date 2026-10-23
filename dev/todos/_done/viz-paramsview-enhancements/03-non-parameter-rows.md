# Phase 3 — Non-parameter rows (`RowSpec` + `extra_rows`)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `ParamsView` recipe) and
> `docs/dev/architecture/viz-controls-and-interactions.md`.  `RowSpec` rows are
> ordinary child control views; no new control kind.

## Goal

Add buttons/status rows that aren't backed by a dataclass field, placeable above
or below the parameter rows.

## Files

- **Edit** `py/pytanga/viz/views/params_view.py` — `RowSpec`, `extra_rows=`,
  ordering, `set_value` for display kinds.
- **Edit** `py/pytanga/viz/__init__.py` — export `RowSpec`.
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **3.1 — `RowSpec`**
  - Define `@dataclass RowSpec(key, ui, value=None, on_click=None, on_change=None,
    position: Literal["above","below"]="below")` in `params_view.py`.
- [x] **3.2 — `extra_rows=` + ordering**
  - `ParamsView.__init__` gains `extra_rows: list[RowSpec] | None = None`.
  - Build each spec's child control (button via `on_click`, others via `value` +
    `on_change`) with `hide_label=True`; render `position="above"` rows before the
    field rows and `"below"` rows after, in `_build_children`/`_serialize`.
- [x] **3.3 — display-row `set_value`**
  - Extend `_value_keys`/`set_value` so `label`/`markdown`/`progress` rows can be
    updated at runtime (and document it does not fire `on_change`).
- [x] **3.4 — export + tests**
  - Export `RowSpec`; test ordering (above/below), button `on_click`, and
    `set_value` on a markdown status row.

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py -q
```

# Phase 5 — Nested `extra_rows` (`GroupUI.extra_rows`, item 5)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (`RowSpec`/`extra_rows`,
> the `ControlUI` model) and the `params_view` serialization.  This adds a field
> to `GroupUI` and forwards it; no new wire format.

## Goal

A nested group can contain its own button/status rows, declared via
`GroupUI(extra_rows=[RowSpec(...)])`.

## Files

- **Edit** `py/pytanga/viz/_params_ui.py` — move `RowSpec` here + add `GroupUI.extra_rows`.
- **Edit** `py/pytanga/viz/views/params_view.py` — import `RowSpec`; forward in `_build_group`.
- **Edit** `py/pytanga/viz/views/__init__.py`, `py/pytanga/viz/__init__.py` — keep
  `RowSpec` exported (source moves, public name unchanged).
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **5.1 — relocate `RowSpec`**
  - Move `RowSpec` from `params_view.py` into `_params_ui.py` (it depends on
    `ControlUI` + `ControlHandler`, both already imported there); keep the public
    export path (`pytanga.viz.RowSpec`) working by re-exporting from the view
    package.
- [x] **5.2 — `GroupUI.extra_rows`**
  - Add `extra_rows: list[RowSpec] | None = None` to `GroupUI`; add `"extra_rows"`
    to `_SHARED_UI_FIELDS` (it is not a control-constructor kwarg).
- [x] **5.3 — forward in `_build_group`**
  - `_build_group` passes `extra_rows=ui.extra_rows` to the nested `ParamsView`.
- [x] **5.4 — tests**
  - A `GroupUI(extra_rows=[RowSpec(...)])` field serializes as a `group` whose
    nested `params_view` rows include the extra rows (in the correct above/below
    order).

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py py/tests/viz/test_params_ui.py -q
```

## Notes

- Relocating `RowSpec` avoids a `_params_ui ↔ params_view` circular import
  (`GroupUI` needs `RowSpec`, `params_view` needs `GroupUI`).

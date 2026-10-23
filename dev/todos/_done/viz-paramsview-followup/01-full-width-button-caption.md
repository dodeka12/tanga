# Phase 1 — Full-width rows + button captions (items 1, 2)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `ControlUI`
> model, the `params_view` row serialization) and the `params-view.js`/`build.js`
> row materialization.  This adds fields to `ControlUI`/`ButtonUI` and a per-row
> `full_width` flag; no new control kind or wire message.

## Goal

`ButtonUI(label="Compute circles")` renders the caption on the button itself, and
`ControlUI(full_width=True)` rows render without a key column (defaulting on for
`ButtonUI`/`MarkdownUI`/`ProgressBarUI`).

## Files

- **Edit** `py/pytanga/viz/_params_ui.py` — `full_width` on `ControlUI`, `label` +
  `full_width=True` on `ButtonUI`, `full_width=True` on `MarkdownUI`/`ProgressBarUI`.
- **Edit** `py/pytanga/viz/views/params_view.py` — track + serialize `full_width`;
  `hide_label`/`label` for buttons.
- **Edit** `py/pytanga/viz/templates/views/params-view.js` — `addRow` full-width.
- **Edit** `py/pytanga/viz/templates/views/build.js` — pass `full_width`.
- **Edit** `py/tests/viz/test_params_ui.py`, `py/tests/viz/test_params_view.py`.

## Steps

- [x] **1.1 — `ControlUI.full_width` + `ButtonUI.label`**
  - Add `full_width: bool = False` to `ControlUI` (after `validate`, before
    `kind`); add `label: str | None = None` to `ButtonUI` and set
    `full_width: bool = True` on `ButtonUI`/`MarkdownUI`/`ProgressBarUI`.
  - Add `"full_width"` and `"label"` to `_SHARED_UI_FIELDS` so `_ui_kwargs` does
    not forward them.
- [x] **1.2 — ParamsView full-width rows**
  - Track `self._full_width_keys: set[str]`; add keys in `_build_children` /
    `_append_row` when `ui.full_width` is truthy.
  - `_serialize` emits `"full_width": True` for those rows.
  - In `_build_child`, set `view.control.hide_label = not bool(ui.full_width)`;
    for `kind == "button"` pass `label=ui.label or ""` (caption) instead of
    `label=""`.
- [x] **1.3 — frontend `addRow` + `build.js`**
  - `build.js` params_view loop passes `full_width: row.full_width` to `addRow`.
  - `addRow` computes `const isFullWidth = full_width || control.typeTag === 'group'`
    and, when full-width, skips the key element + adds `.tanga-params-row-group`
    (reuse the existing full-width grid rule).
- [x] **1.4 — tests**
  - `ButtonUI(label=…)` serializes `label` on the button + `full_width` on the row;
    `MarkdownUI()`/`ProgressBarUI()` rows are full-width by default;
    `hide_label` is off for full-width buttons and on otherwise.  Update
    `test_kinds_and_fields` field lists.

## Validation

```bash
uv run pytest py/tests/viz/test_params_ui.py py/tests/viz/test_params_view.py -q && node js/dev/tests/check-syntax.mjs
```

## Notes

- Full-width value controls (slider/dropdown/…) are out of scope: the flag
  exists on `ControlUI` but full-width rendering is only exercised for
  button/markdown/progress rows (a full-width slider would show an empty/id
  label — accepted, undocumented edge case).

# Phase 7 — Spec gaps: `(value, label)`, units, validation

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (control fields +
> frontend factories).  These are additive `ControlUI` fields + factory tweaks.

## Goal

Dropdown `(value, label)` pairs, a unit/suffix on numeric controls, and a
`validate=` hook.

## Files

- **Edit** `py/pytanga/viz/_params_ui.py` — `DropdownUI.options` pairs,
  `ValueEditUI.unit`, `ControlUI.validate`.
- **Edit** `py/pytanga/viz/views/params_view.py` — apply validation/coercion.
- **Edit** `py/pytanga/viz/templates/controls/dropdown.js` — render `(value, label)`.
- **Edit** `py/pytanga/viz/templates/controls/value-edit.js` — unit suffix.
- **Edit** `py/tests/viz/test_params_ui.py`, `py/tests/viz/test_params_view.py`.

## Steps

- [x] **7.1 — `(value, label)` options**
  - `DropdownUI.options: list[str | tuple[str, str]] | None`; serialize as
    `[{"value","label"}]`; `dropdown.js` renders the label as `<option>` text.
- [x] **7.2 — unit/suffix**
  - `ValueEditUI.unit: str | None`; `value-edit.js` appends the unit after the input.
- [x] **7.3 — `validate`**
  - `ControlUI.validate: Callable[[Any], bool | str] | None`; on change, reject
    (revert + report) or coerce invalid input before storing.
- [x] **7.4 — tests**
  - `(value, label)` serializes + resolves; unit is shown; `validate` rejects/clamps.

## Validation

```bash
node js/dev/tests/check-syntax.mjs && uv run pytest py/tests/viz/test_params_ui.py py/tests/viz/test_params_view.py -q
```

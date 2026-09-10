# Phase 4 — Frontend types, editors & alignment

## Goal

Render and edit cells per column type, apply type-driven alignment, and apply
the received view state (widths, row height, sort) on render.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`

## Steps

- [x] **4.0 — extract `createTable` into `controls/table.js`**
  - Move `createTable` + its table-only DOM helpers out of `controls-panel.js`
    into a new `py/pytanga/viz/templates/controls/table.js` (mirroring the
    `renderers/*.js` per-entity split and the existing `table-grid.js` pure-helper
    split). Only `views/table-view.js` imports `createTable`; update it to import
    from `../controls/table.js`.
  - `controls-panel.js` exposes the shared helpers the table needs
    (`sendControlEvent`, `createIconElement`, `resolveUndoRedoAction` are already
    exported; add `registerControl(id, entry)` and `applyTooltip` for
    `_controlRegistry`/`_applyTooltip`). One-way dependency, no cycle.
  - `node --check` both files; no behaviour change.

- [x] **4.1 — ingest new fields (`controls/table.js`)**
  - In `createTable`, read and store `ctrl.column_types`, `ctrl.column_widths`,
    `ctrl.row_height`, `ctrl.sort` (with safe defaults). Add a small
    `columnKind(colIndex)` helper (→ `"number"|"string"|"bool"|"enum"`) and
    `enumValues(colIndex)`.

- [x] **4.2 — per-type cell rendering (`controls/table.js`)**
  - `renderBody`: bool cells render an `<input type="checkbox">` (checked when the
    value is `"true"`); other cells render text as today. Set `td.style.textAlign`
    from the kind (`number`→right, `string`/`enum`→left, `bool`→center).

- [x] **4.3 — bool toggle (`controls/table.js`)**
  - Clicking a bool cell's checkbox toggles and commits immediately via
    `sendControlEvent('control:cell_change', …)` with `"true"`/`"false"`; update
    the local `rows` + re-render.

- [x] **4.4 — enum editor (`controls/table.js`)**
  - `openEditor` for an enum column builds a `<select>` with the allowed values
    (current value selected); commit on change/blur/Enter, cancel on Escape, like
    the text editor.

- [x] **4.5 — number validation (`controls/table.js`)**
  - On commit, a `number` column rejects a non-numeric string (revert to the
    original value and keep the editor open or show a subtle error).

- [x] **4.6 — apply view state + alignment inherit (`controls/table.js`, `table.css`)**
  - On render/`apply`, apply `column_widths` (fit relative weights to
    `avail * colScale`), `row_height` (set `--tanga-table-row-height`), and
    `sort` (set `sortState` + re-render).
  - Add `.tanga-cell .tanga-table-editor { text-align: inherit; }` so the editor
    matches the cell alignment; style `.tanga-cell-bool`/checkbox if needed.

- [x] **4.7 — smoke**
  - Browser smoke: numeric/bool/enum columns render with correct alignment and
    editors (checkbox toggles, select opens, number rejects bad input).

## Validation

`node --check py/pytanga/viz/templates/controls-panel.js` + browser smoke
(Playwright probe, deleted after use).

## Notes

- `apply` (backend push) must also re-apply `column_widths`/`row_height`/`sort`,
  so `set_value`/undo pushes restore the layout.

# Phase 5 — Frontend keyboard shortcuts

## Goal

Wire **Ctrl+Z** (undo) and **Ctrl+Shift+Z** / **Ctrl+Y** (redo) in `createTable`
so they send `control:undo` / `control:redo` to the backend. No Undo/Redo
buttons; the grid shows only the table.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- New: `dev/src/js-tests/table-keyboard.test.mjs`

## Steps

- [x] **5.1 — `_CONTROL_EVENTS` entries**
  - Add `'control:undo': 'undo'` and `'control:redo': 'redo'` to the
    `_CONTROL_EVENTS` map (line ~1036).

- [x] **5.2 — Pure key-decision helper**
  - Extract a small helper (module-local or exported) that maps a keyboard-event
    shape `{ ctrlKey, shiftKey, key }` to `'undo' | 'redo' | null`:
    Ctrl+Z → undo; Ctrl+Shift+Z or Ctrl+Y → redo; otherwise `null`. This keeps
    the logic unit-testable without a Tabulator/DOM.

- [x] **5.3 — Keydown listener in `createTable`**
  - Attach a `keydown` listener to the table `wrapper` (or the Tabulator
    container). Use the helper from 5.2; on `'undo'`/`'redo'` call
    `sendControlEvent('control:undo'|'control:redo', ctrl.id, null)` and
    `preventDefault()`.
  - Skip when focus is inside the Tabulator cell-editor input (e.g. check
    `e.target.closest('.tabulator-editor input')` or that
    `document.activeElement` is an editor input) so native text undo still works
    mid-edit.

- [x] **5.4 — JS unit test (`table-keyboard.test.mjs`)**
  - Import the helper and assert the mapping: Ctrl+Z → `undo`, Ctrl+Shift+Z and
    Ctrl+Y → `redo`, plain Z / Ctrl+other → `null`.

## Validation

`node --test dev/src/js-tests/table-keyboard.test.mjs && node --input-type=module --check py/pytanga/viz/templates/controls-panel.js`

## Notes

- `sendControlEvent(type, id, null)` omits the `value` key (see the existing
  `null`/`undefined` guard), producing the `data: {}` envelope the backend
  expects.
- Follow the existing `createTable` style; the keydown listener must not break
  the existing `tabEndNewRow` / `keybindings` / `selectableRange` config.
- Manual browser check: run `table_editing.py`, edit a cell, press Ctrl+Z and
  observe the grid revert.

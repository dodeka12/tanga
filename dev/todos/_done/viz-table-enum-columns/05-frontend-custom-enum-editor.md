# Phase 5 — Frontend: `custom` edit-time options

## Goal

When a `"custom"` cell enters edit mode, request its dropdown options from the
backend and populate the editor when the targeted reply arrives; suppress the
type-change context menu for `"custom"` columns.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/controls/table.js`

## Steps

- [x] **5.1 — `_CONTROL_EVENTS` + `applyEnumOptions`**
  - In `controls-panel.js`, add `'control:enum_options': 'enum_options'` to
    `_CONTROL_EVENTS`.
  - Export `applyEnumOptions(id, requestId, values)` that looks up
    `_controlRegistry[id]` and calls `entry.applyEnumOptions?.(requestId, values)`
    (no-op when absent).

- [x] **5.2 — `viewer.js` handles the reply**
  - Import `applyEnumOptions` alongside `applyControlValue`.
  - Add `if (msg.type === 'enum_options') { applyEnumOptions(msg.id, msg.request_id, msg.values); return; }`.

- [x] **5.3 — `table.js` sends the request on edit**
  - In `openEditor`, add a `kind === 'custom'` branch **before** the enum/text
    branches: create a disabled `<select class="tanga-table-editor">` with a
    "Loading…" option, generate `const requestId = ++enumRequestSeq` (a new
    per-table closure counter), store
    `pendingEnum = { requestId, td, ri, ci, original, widget }`, and send
    `sendControlEvent('control:enum_options', ctrl.id, { col: ci, row: ri, request_id: requestId })`.

- [x] **5.4 — `table.js` applies the reply**
  - In `registerControl(ctrl.id, {...})`, add
    `applyEnumOptions(requestId, values)` that, when
    `pendingEnum && pendingEnum.requestId === requestId`, replaces the loading
    widget with a `<select>` of `values` (plus the current-value fallback),
    selects the original value, re-focuses, and clears `pendingEnum`.
  - Guard against a reply arriving after the editor was closed/committed.

- [x] **5.5 — Suppress the type menu for `custom`**
  - At the top of `openTypeMenu`, `if (current === 'custom') return;`.

## Validation

```
node --check py/pytanga/viz/templates/controls/table.js; node --check py/pytanga/viz/templates/controls-panel.js; node --check py/pytanga/viz/templates/viewer.js
```

## Notes

- Keep the existing editor finish/blur/keydown wiring so the populated `<select>`
  behaves like the `enum` editor (Enter/Tab/Escape, `finish`).
- The reply is targeted, so no `control_update` re-render competes with the open
  editor.

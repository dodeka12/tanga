# Phase 2 — Frontend editor view

## Goal

Add a reusable `EditorView` (derived from `View`) mounted in the shared
`OverlayView`, and wire the `editor_define` / `editor_closed` messages.

## Steps

- [x] **2.1 — `templates/views/editor-view.js`: `EditorView extends View`**
  - Constructor `{ id, label = '', value = '', onClose = null }`.
  - DOM: a label, a `resize: vertical` `<textarea>` (pre-filled with `value`),
    and ✓ / ✕ buttons; `pointer-events: auto`.
  - ✓ → `this.onClose(this.editorId, textarea.value)`; ✕ →
    `this.onClose(this.editorId, null)`.

- [x] **2.2 — `templates/editor.js`: manager**
  - `setWebSocket(ws)`, `handleEditorDefine(msg)`: build an `EditorView`,
    `getOverlay().addChild(view)`, and on close send
    `{ type: "editor_closed", id, text }` and remove/destroy the view.

- [x] **2.3 — Wiring**
  - `viewer.js`: import `setEditorWebSocket`/`handleEditorDefine` from
    `./editor.js`; call `setEditorWebSocket(ws)`; route `editor_define`.
  - `viewer.html`: add `<script type="module" src="editor.js">`.

- [x] **2.4 — Validate**
  - `node --check` on `editor.js`/`editor-view.js`; browser smoke
    (`open_editor("e", value="$a_e$", on_close=...)`).

## Validation

`node --check py/pytanga/viz/templates/editor.js py/pytanga/viz/templates/views/editor-view.js`
+ browser smoke.

## Notes

- Follows the `banner.js` / `file-browser.js` manager pattern.
- No icon-font dependency (Unicode ✓/✕).

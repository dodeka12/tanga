# Phase 8 — Dialog frontend (`dialog-view.js`, `dialog.js`, routing)

## Goal

Render the dialog in the browser: a title bar + borderless close button, with
the serialized `content` view subtree mounted inside; close sends
`sendEvent(id, "close")`.

## Files

- New: `py/pytanga/viz/templates/views/dialog-view.js`
- New: `py/pytanga/viz/templates/dialog.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/viewer.html` (if script includes are explicit)

## Steps

- [x] **8.1 — `dialog-view.js` (`DialogView extends View`)**
  - Accept `{ id, title, content, align_x, align_y, dismissable }`; style like
    `banner-view.js` (dark panel, align anchor, `pointerEvents:auto`).
  - Build title + borderless close ✕ (click → `sendEvent(id, "close")` +
    unmount), then mount `buildViewTree(content)` into a content container.
  - Clean up registered control entries (owner `dialog`) on unmount.

- [x] **8.2 — `dialog.js` manager**
  - Mirror `banner.js`: `handleDialogDefine` / `handleDialogRemove` /
    `handleDialogClear`, owning an id → `DialogView` map on `getOverlay()`.

- [x] **8.3 — `viewer.js` routing**
  - Add a `dialog_define` / `dialog_remove` / `dialog_clear` block (global first,
    then scene-scoped fall-through), mirroring the `banner_*` block.

- [x] **8.4 — Smoke**
  - New `dev/src/js-tests/dialog-view-smoke.html`: assert title/content render
    and clicking the ✕ (or a close button inside content) triggers `close`.

## Validation

`node --check py/pytanga/viz/templates/views/dialog-view.js && node --check py/pytanga/viz/templates/dialog.js && node --check py/pytanga/viz/templates/viewer.js`

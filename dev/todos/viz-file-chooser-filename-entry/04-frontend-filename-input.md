# Phase 4 — Editable filename input + glob filter (frontend)

## Goal

Replace the dialog's read-only path line with an editable filename `<input>`,
drive the server-side glob filter from it, and send the typed full path on
accept.

## Files

- Edit: `py/pytanga/viz/templates/views/file-chooser-view.js`
- Edit: `py/pytanga/viz/templates/views/file-chooser-dialog-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`

## Steps

- [ ] **4.1 — `FileChooserView`: pattern + navigate event**
  - Accept `existing_only` in the constructor (mirror `folders_only`).
  - Store `_pattern = ""`; make `_navigate(path)` send
    `{ path, pattern: this._pattern }`; add a public `filter(pattern)` that sets
    `_pattern` and re-navigates to `_currentPath`.
  - In `updateListing`, emit `this.emit("navigate", { path, files })` where
    `files` = non-directory entry names.
- [ ] **4.2 — `FileChooserDialogView`: filename input**
  - Read `existing_only` from `this.contentNode.existing_only ?? true`.
  - Replace `_pathEl` (`div`) with a filename `<input type="text">` plus a
    directory label; keep `_selectedPath` handling.
  - Track `_directory`, `_fileNames`, `_filename`; listen for the content view's
    `navigate` (capture directory + files) and `select` (set input to basename).
  - On input: set `_filename`, call `this._contentView.filter(value)`, update OK.
  - `_updateOk()`: open mode → `_filename` non-empty and in `_fileNames`; save
    mode → `_filename` non-empty.
  - OK / double-click accept → `sendEvent(this.dialogId, "accept",
    { value: <full path> })` (join `_directory` + `_filename`).
- [ ] **4.3 — `build.js`**
  - Pass `existing_only: node.existing_only` into `new FileChooserView(...)`.

## Validation

```
cd js/dev && node tests/check-syntax.mjs
```

## Notes

- `_join(dir, name)`: use `dir ? dir + "/" + name : name` (the backend resolves
  and normalises paths).
- The dialog still listens for the listing's `accept` (double-click) so existing
  click-pick behavior keeps working.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

# Phase 6 — File chooser: highlight, double-click, filter, folder select

> **Independent phase** — does not depend on phases 1–5.

## Goal

Upgrade the file chooser so a single click highlights the selected entry,
double-click accepts it, the `accept` string filters the listing to matching
file types, and `folders_only=True` turns it into a folder picker.

## Files

- Edit: `py/pytanga/viz/_file_browser.py` (`list_directory` → `accept`, `folders_only`)
- Edit: `py/pytanga/viz/_controls.py` (`FileChooser` → `folders_only`)
- Edit: `py/pytanga/viz/views/control_views.py` (`FileChooserView` → `folders_only`)
- Edit: `py/pytanga/viz/_dialog.py` (`FileChooserDialog` → `folders_only`, pass-through)
- Edit: `py/pytanga/viz/_layout.py` (`file_browser_navigate` passes `accept`/`folders_only`)
- Edit: `py/pytanga/viz/templates/views/file-chooser-view.js` (highlight, dblclick, folder UI)
- Edit: `py/pytanga/viz/templates/views/file-browser-view.js` (same)
- Edit: `py/pytanga/viz/templates/views/build.js` (pass `folders_only` to the view)
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (document the new contract)
- Edit: `py/tests/viz/test_file_chooser.py`

## Steps

- [x] **6.1 — Backend: filter + folders**
  - `list_directory(path, *, root=None, show_hidden=False, accept="", folders_only=False)`:
    filter non-dir entries by `accept` (comma/space-separated, case-insensitive
    extension list; empty = all) and, when `folders_only`, drop files entirely.
- [x] **6.2 — Model + serialization**
  - Add `folders_only: bool = False` to `FileChooser`, `FileChooserView`, and
    `FileChooserDialog`; serialize it and pass it through `build_dialog` →
    `FileChooserView`.
- [x] **6.3 — Dispatch**
  - In `_layout.py`, resolve the control's `accept`/`folders_only` and pass them
    to `list_directory` in the `file_browser_navigate` handler.
- [x] **6.4 — Frontend: highlight + double-click**
  - Track `_selectedPath`; single-click a selectable entry sets it and adds a
    `selected` CSS class (clear the previous highlight) without accepting;
    `dblclick` on a selectable entry accepts it (`file_browser_select` /
    `onSelect`).  Directories still navigate on single-click.
- [x] **6.5 — Frontend: folder mode**
  - When `folders_only`, list only directories; add a "Select this folder"
    action (path-bar button) that accepts the current directory.
- [x] **6.6 — Tests + rebuild**
  - Backend tests for `accept` filtering and `folders_only`; assert serialization
    and dispatch carry the new fields.
  - `uv run python tools/build-viewer-js.py` and JS syntax/test checks.

## Validation

```
uv run pytest py/tests/viz/test_file_chooser.py -q \
  && uv run ruff check py/pytanga/viz/_file_browser.py py/pytanga/viz/_controls.py py/pytanga/viz/views/control_views.py py/pytanga/viz/_dialog.py \
  && uv run python tools/build-viewer-js.py --check \
  && cd js/dev && node tests/check-syntax.mjs && node --test 'tests/*.test.mjs'
```

## Notes

- The existing `accept` field already flows to the frontend (`node.accept`) but
  is unused; this phase makes it meaningful on the backend instead.
- "Select" semantics: single-click = highlight, double-click = accept.  In
  folder mode, files are hidden and the current directory is acceptable.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

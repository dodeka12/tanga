# File Chooser Filename Entry + Save Mode — Overview

**Created:** 2026-10-01 | **Status:** Done | **Branch:** `feat/calibrated-pane-interaction`

## Goal

Make the `FileChooserDialog` accept a typed **filename** (not only click-picked
files), use that filename as a live glob filter over the selected folder, and
add an open-vs-save mode so "Save As…" can return names that do not exist yet.
The image-labeling app then appends `.json` to a save filename when no
extension is given.

## Architecture (short)

- `FileChooser` (`py/pytanga/viz/_controls.py`), `FileChooserView`
  (`views/control_views.py`), and `FileChooserDialog` (`_dialog.py`) gain one
  flag — `existing_only: bool = True` — serialized and threaded end-to-end.
  `True` (open mode) only accepts filenames that exist in the listing; `False`
  (save mode) accepts any non-empty filename.
- `list_directory` (`_file_browser.py`) gains `pattern: str = ""`, a single
  case-insensitive glob applied to non-directory entries **in addition to** the
  static `file_filter`.  The `file_browser_navigate` handler forwards an
  optional `pattern` from the payload.
- The `accept` event may now carry an explicit `value` (the full path).  The
  dialog sends it; `_on_dialog_accept` prefers it and falls back to
  `ctrl.get_value()` (unchanged click-pick flow).
- Frontend: the dialog footer's read-only path line becomes an editable
  filename `<input>` + a directory label.  The listing view (`FileChooserView`)
  learns a `filter(pattern)` method and emits a `navigate` event carrying the
  current directory + non-directory names so the dialog can enable/disable OK.

## Fixed contract (up front)

- Control field: `existing_only: bool = True` — always serialized (like
  `folders_only`) as `"existing_only": <bool>` on `FileChooser`, `FileChooserView`,
  and `FileChooserDialog`.
- `list_directory(..., pattern: str = "")` — `pattern` is always treated as a
  glob via `fnmatch.fnmatchcase(name.lower(), pattern.lower())`; empty = no
  extra filter.  Does **not** change `file_filter` semantics.
- `file_browser_navigate` payload gains optional `pattern: str`.
- `accept` payload gains optional `value: str` (the full path to accept).
- OK enablement: `existing_only=True` → filename non-empty **and** listed;
  `existing_only=False` → filename non-empty.  OK sends
  `sendEvent(dialogId, "accept", { value: join(directory, filename) })`.

## Decisions (confirmed)

- Use a boolean `existing_only` (parallel to `folders_only`), not a `mode` string.
- Filename input holds the **basename**; the directory is shown by the listing's
  path bar; the dialog joins them into the full path on accept.
- Filtering stays **server-side** (the frontend never reads the filesystem).
- The bare `FileChooserView` (embedded in arbitrary layouts, no OK button) keeps
  its current select-only contract; the filename input + mode live in the dialog.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-model-existing-only.md](./01-python-model-existing-only.md) | `existing_only` on `FileChooser` / `FileChooserView` / `FileChooserDialog` + serialization |
| 2 | [02-list-glob-pattern.md](./02-list-glob-pattern.md) | `list_directory(pattern=…)` + forward `pattern` in the navigate handler |
| 3 | [03-accept-explicit-value.md](./03-accept-explicit-value.md) | Thread an explicit `value` through the dialog accept path |
| 4 | [04-frontend-filename-input.md](./04-frontend-filename-input.md) | Editable filename input, glob filter, OK enablement, accept value |
| 5 | [05-app-save-as.md](./05-app-save-as.md) | Wire Save As (save mode, `.json` filter + extension) in the app |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Architecture + example docs, changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_file_chooser.py -q`
- Lint/type: `uv run ruff check <files>` / `uv run ty check`
- Frontend: `cd js/dev && node tests/check-syntax.mjs`
- Docs: `uv run python tools/generate-example-docs.py --check` and
  `uv run mkdocs build --strict`

## Non-goals

- No new wire protocol, host, or control pattern — only optional fields on the
  existing file-chooser events and one new control flag.
- No filename input on the bare `FileChooserView` (embedded listing stays
  select-only).
- No drag-drop, thumbnails, recursive search, or virtualised listing.
- No client-side filtering fallback (server-side only).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

# Viz File Chooser — Overview

**Created:** 2026-08-26 | **Status:** Planned | **Branch:** `feat/small-extensions`

## Goal

Add a **file chooser** control that can be shown programmatically from Python:

- a text field for a file **path**, plus a "Browse…" button that opens a
  **custom file browser**;
- the browser is driven by the **backend** (which runs on the Linux filesystem
  and supplies the folder/file listings over the existing WebSocket), so it can
  return **real absolute paths** — unlike the browser's native file dialog;
- the browser can be **opened directly from the backend** (`open_file_chooser`),
  with no native dialog / user-gesture requirement;
- when a file is selected or a path is typed, an event fires for which a
  backend handler can be registered (`on_change(path, event)`);
- the dialog is **modal** — the surrounding visualization is grayed out and
  blocked, exactly like a non-dismissable banner.

## Architecture (short)

- **Two-layer mirror.** Python `FileChooser` dataclass + serializer in
  `py/pytanga/viz/_controls.py`; JS control (`createFileChooser`) + dialog
  (`FileBrowserView`) in `templates/`.
- **Backend-supplied listing.** The frontend never reads the filesystem; it
  asks the backend (`file_browser_navigate`) and renders the reply
  (`file_browser_listing`).  The backend runs on the machine whose files are
  browsed, so the paths it sends are real.
- **View base-class + shared overlay.** `FileBrowserView` (dialog) and
  `FileChooserView` (control) both extend `View`.  The dialog mounts into the
  **same full-screen `OverlayView`** the banners use (extracted into a shared
  `templates/overlay.js` singleton).  The dialog is modal: a dimmed,
  interaction-blocking backdrop like `BannerView(dismissable=False)`.
- **Reuse the control dispatch.** Selecting/typing a path sends
  `control:change` / `file_browser_select`, dispatched through the existing
  `_handler_registry`.

## Wire contract (fixed up front)

### Control def (inside `controls_define`)

```json
{ "id": "fc1", "kind": "file_chooser", "label": "Data file",
  "value": "/home/me/data.csv", "placeholder": "Path…", "root": "/home/me",
  "accept": "" }
```

`value` = current path; `root` = browse root (defaults to the home directory
server-side); `accept` = reserved (unused by the custom browser).

### `file_browser_show` (server → client)

```json
{ "type": "file_browser_show", "scene": null, "control_id": "fc1",
  "path": "/home/me" }
```

Opens the modal browser at *path* (or the control's `value`, or `root`).

### `file_browser_navigate` (client → server)

```json
{ "type": "file_browser_navigate", "control_id": "fc1", "path": "/home/me/src" }
```

### `file_browser_listing` (server → client)

```json
{ "type": "file_browser_listing", "control_id": "fc1", "path": "/home/me/src",
  "entries": [
    { "name": "data.csv", "path": "/home/me/src/data.csv", "is_dir": false },
    { "name": "lib",      "path": "/home/me/src/lib",      "is_dir": true }
  ],
  "error": null }
```

`entries` dirs-first, alphabetical.  `error` ∈ `null | "missing" | "permission"`.

### `file_browser_select` (client → server)

```json
{ "type": "file_browser_select", "control_id": "fc1", "path": "/home/me/src/data.csv" }
```

Backend updates the control `value` and calls `on_change(path, event)`.

### `file_browser_close` (server → client)

```json
{ "type": "file_browser_close", "control_id": "fc1" }
```

### Typed path (client → server)

Reuses `control:change` `{ control_id, value }` → `on_change(path, event)`.

## Decisions (confirmed)

- Browse root = **home directory** by default, overridable per control via
  `root=`.  The text field accepts any absolute path regardless of `root`.
- Files only (directories navigate); single selection; hidden files hidden by
  default (`show_hidden=` option).
- The dialog is **modal** (grayed-out, blocking backdrop) — explicit
  Select/Cancel, no click-away.
- The dialog is **global** (one open at a time, in the shared overlay); the
  control is scene-scoped; `control_id` ties them together.
- No native `<input type="file">` — the custom browser is the only picker.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-file-chooser-model.md](./01-python-file-chooser-model.md) | `list_directory`, `FileChooser` dataclass + serialization (+ tests) |
| 2 | [02-visualizer-file-chooser-api.md](./02-visualizer-file-chooser-api.md) | `add_file_chooser`/`open_file_chooser`, navigate/select dispatch, `on_change` (+ tests) |
| 3 | [03-frontend-file-browser-view.md](./03-frontend-file-browser-view.md) | shared `getOverlay()`, `FileBrowserView` (modal), `file-browser.js`, `createFileChooser`, routing |
| 4 | [04-file-chooser-view-layout.md](./04-file-chooser-view-layout.md) | `FileChooserView extends ControlView` (views.py + JS + build.js) |
| 5 | [05-docs-example-changelog.md](./05-docs-example-changelog.md) | example, docs, changelog, full validation |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (new `test_file_chooser.py`).
- **JS:** `node --input-type=module --check` on new modules; DOM behavior
  verified live via the Python example (the viewer serves modules over HTTP).
- Every phase ends with a runnable validation command before the next starts.

## Non-goals

- File content upload (the backend only receives a path).
- Multi-select, directory selection, rename/delete, or any file *management*.
- Native `<input type="file">` integration.

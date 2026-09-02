# Changes since version 1.16.0

## New Features
- **`FileChooserDialog`** — a full file-open dialog (a `FileChooserView`
  listing plus a path line and OK/Cancel), passed to `viz.show_dialog(...)`.
  Selecting a file fills the path line (no close); `OK` fires `on_accept(path)`
  and closes, while `Cancel`/✕ fire `on_close`.
- **Dialog `width`/`height` + drag-to-resize corner** — `show_dialog(...,`
  `width=..., height=...)` sizes a dialog (px or percent-of-viewport), and every
  dialog now has a bottom-right resize handle.  Dialogs no longer shrink-wrap
  and jump when their content changes.

## Breaking Changes
- **`FileChooserView` no longer renders a path field or "Browse…" button** —
  it is now just the file-selection (directory listing) view, embeddable in any
  view container.  A path display, edit field, and browse button must be
  composed by the caller (e.g. a `TextFieldView` + `ButtonView`).

## Bug Fixes
- **Menu bar renders horizontally, left-aligned** — a `mode="bar"` menu now
  defaults to a horizontal row (items left-aligned like a normal menu bar)
  instead of a vertical column.
- **Menu-bar submenus open downwards with plain labels** — a nested `MenuView`
  inside a `mode="bar"` menu now opens below its label (flipping above near the
  viewport bottom) and renders as a plain menu-bar item without a chevron,
  instead of opening sideways like a dropdown submenu.
- **File-chooser "Up" steps one level on every platform** — the parent
  directory is now computed by the backend with `pathlib.Path` and sent in each
  listing, so the "Up" button works for both `/` and `\` paths (no more jumping
  to the root on Windows).

## Refactor
- **File-browser manager is a class with a control-id registry** — the
  frontend `file-browser.js` single-global-view singleton is replaced by a
  `FileBrowserManager` that routes `file_browser_listing` pushes by
  `control_id` to embedded `FileChooserView`s or the modal browser, which are
  created and released per use.
- **View `min`/`max` size specs render as CSS** — `View` now applies `min/max`
  width/height specs as inline CSS on its element, so they take effect outside
  a `SplitView` (dialogs, overlays, standalone content).

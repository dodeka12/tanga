# Phase 3 — Frontend `FileBrowserView` (modal) + control factory

## Goal

Build the modal file-browser dialog as a `View` in the shared overlay, plus the
`createFileChooser` control and message routing.

## Steps

- [x] **3.1 — Shared overlay (`templates/overlay.js`, new)**
  - Move the `OverlayView` singleton out of `banner.js` into
    `getOverlay()` (lazily creates + mounts the `OverlayView` on
    `document.body`).
  - `banner.js` switches to `getOverlay()` (no behavior change).

- [x] **3.2 — `FileBrowserView extends View` (`templates/views/file-browser-view.js`, new)**
  - Modal chrome like `BannerView(dismissable=False)`: a dimmed,
    `pointer-events:auto` backdrop (grays out + blocks the scene) + a centered
    card.
  - Content: a path bar (current directory + "Up" button), an entry list
    (directories navigate, files select), Cancel/Close buttons.
  - `onNavigate(path)` / `onSelect(path)` / `onClose()` callbacks provided by
    the manager.

- [x] **3.3 — `templates/file-browser.js` (new manager)**
  - Module state: active `FileBrowserView`, `_ws` (`setWebSocket`), current
    `control_id`/`path`.
  - `handleFileBrowserShow(msg)`, `handleFileBrowserListing(msg)`,
    `handleFileBrowserClose(msg)`; sends `file_browser_navigate` /
    `file_browser_select` / `file_browser_close`.

- [x] **3.4 — `createFileChooser` (`controls-panel.js`)**
  - Text input (path) + "Browse…" button. Typing →
    `sendControlEvent('control:change', id, value)` (debounced). Browse →
    open the dialog at the current value (sends `file_browser_navigate`).
  - Register the control id so the dialog knows which control it serves.

- [x] **3.5 — Routing (`viewer.js`)**
  - Route `file_browser_show` / `file_browser_listing` / `file_browser_close`
    to `file-browser.js` (global), before scene routing.

- [ ] **3.6 — Manual check**
  - Phase 5 example — open the browser, navigate, select; confirm the modal
    backdrop grays out and blocks the scene.

## Validation

`node --input-type=module --check` on touched modules + live viewer example.

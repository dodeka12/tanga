# Phase 4 — Unified event envelope + dispatcher

## Goal

One client→server envelope and one dispatcher for all "user action" messages;
collapse the per-feature handler dicts (`_banner_close_handlers`,
`_editor_close_handlers`) into the `(id, event)` registry.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/templates/viewer.js`, `controls-panel.js`,
  `file-browser.js`, `banner.js`, `editor.js`
- Edit: tests

## Steps

- [ ] **4.1 — Backend `_dispatch_event(target, event, scene, data)`**
  - One entry point that looks up `(target, event)`, builds the typed event
    (`ControlEvent`/`TableCellChange`/…), and awaits the handler.
  - Route `control:*`, `banner_closed`, `editor_closed`, `file_browser_*`
    through it. Keep `server.py` routing stable during this phase.

- [ ] **4.2 — Fold banner/editor handlers into the registry**
  - Register banner close as `(banner_id, "close")` and editor close as
    `(editor_id, "close")`; remove `_banner_close_handlers` /
    `_editor_close_handlers`.

- [ ] **4.3 — Frontend sends the unified envelope**
  - `sendControlEvent` and the file-browser/banner/editor senders emit
    `{ type: "event", target, event, scene, data }`; the server accepts both the
    legacy and unified forms during migration.

- [ ] **4.4 — Tests**
  - Backend: `_dispatch_event` routes each kind; banner/editor close dispatch.
  - Frontend: smoke pages still function.

## Validation

`uv run pytest py/tests/viz/ -q && node --test dev/src/js-tests/`

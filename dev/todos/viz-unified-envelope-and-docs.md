# Viz: Unified client→server event envelope + close unification + docs

**Date:** 2026-08-31 · **Status:** Planned · **Branch:** `fix/file-chooser-bug`

**Follow-on to:** [`viz-unified-controls/`](viz-unified-controls/) (phases 1–7, done).

## Goal

Finish the frontend side of the unified controls/interactions architecture:

1. One client→server envelope `{type:"event", target, event, data}` sent through a
   single `sendEvent` helper; migrate the control/banner/editor/file-browser senders.
2. Unify `banner_closed` / `editor_closed` into one `close` event carrying the
   control's `value` (the editor's text; `None` for the value-less banner).
3. Document the architecture under `docs/dev/` and reference it in `.clinerules`.

## Steps

- [ ] **1 — Backend close unification** (`visualizer.py` + `test_banner.py`)
  - One `"close"` branch (aliases `banner_closed`/`editor_closed`) that passes
    `value` (editor text, or `None`) and is one-shot for both.
- [ ] **2 — Frontend `events.js` + sender migration** (`templates/*`)
  - `events.js` (`setWebSocket`, `sendEvent(target, event, data)`); migrate
    `sendControlEvent`/`throttledSend`/`throttledFlush`, `banner.js`,
    `three-view.js`, `editor.js`, `file-browser.js`.
- [ ] **3 — Server envelope acceptance** (`server.py`)
  - Route `{type:"event", target, event, data}` by `event` name; keep legacy
    `control:*`/`banner_closed`/… as accepted aliases.
- [ ] **4 — Tests** — envelope routing (pytest) + `sendEvent` shape (node:test).
- [ ] **5 — Docs** — `docs/dev/architecture/viz-controls-and-interactions.md`
  + `mkdocs.yml` nav + `docs/dev/index.md`.
- [ ] **6 — `.clinerules/rules.md`** — rule pointing new frontend elements at the
  architecture doc.
- [ ] **7 — Changelog** — Breaking Change (banner `on_close` now receives `None`)
  + New Features/Refactor bullets.
- [ ] **8 — Full validation** — pytest + node --test + mkdocs build --strict.

## Validation

`uv run pytest py/tests/viz/ -q && node --test dev/src/js-tests/*.test.mjs && uv run mkdocs build --strict`

## Notes

- Interactions keep the `interaction:` event namespace (coalescing + single-arg
  handler); they already share the `(id, event)` registry (phase 6). They route
  through the same server envelope branch.

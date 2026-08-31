# Viz Editor View — Overview

**Created:** 2026-08-27 | **Status:** Done | **Branch:** `feat/more-controls`

## Goal

Add a reusable, general-purpose **multi-line text editor** to the viewer.  The
editor is a frontend `EditorView` (derived from the generic `View` base) that
is mounted into the existing full-screen `OverlayView` container.  It is
**not** tied to annotations: closing it simply invokes a user-supplied Python
handler with the edited text (or `None` when discarded), and the handler
decides what to do (e.g. `set_annotation(...)`).

## Architecture (short)

- **`EditorView extends View`** (frontend): a textarea + ✓ (keep) / ✕ (discard)
  buttons, mounted via `getOverlay().addChild(...)` like banners/file-browser.
- **One message each way**:
  - `editor_define` (server → client) opens an editor: `{id, label, value}`.
  - `editor_closed` (client → server) reports the close: `{id, text}` (`text`
    is `null` on discard).
- **`Visualizer.open_editor(id, *, label="", value="", on_close=None)`** opens
  an editor and registers `on_close(text, event)`; the handler runs on the
  server loop when the editor closes.
- **No auto-update.**  The handler is the only consumer — it may call
  `set_annotation`, store the text, or do anything else.  The annotation gains
  no edit affordance.

## Canonical wire contract (fixed up front)

### `editor_define` (server → client)

```json
{ "type": "editor_define", "id": "editor", "label": "Edit text", "value": "initial $a_e$" }
```

### `editor_closed` (client → server)

```json
{ "type": "editor_closed", "id": "editor", "text": "edited $a_e$" }
```

`text` is `null` when the user discards (✕).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-editor-api.md](./01-python-editor-api.md) | `open_editor` + handler registry + `editor_closed` dispatch + `server.py` routing (+ tests) |
| 2 | [02-frontend-editor-view.md](./02-frontend-editor-view.md) | `EditorView` + `editor.js` manager + viewer wiring |
| 3 | [03-docs-changelog.md](./03-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_editor.py -q` (new) plus the
  existing `test_banner.py` (mirrors the `banner_closed` dispatch pattern).
- **JS (DOM module):** `editor-view.js` / `editor.js` are DOM-heavy — validated
  via `node --check` (syntax) plus a browser smoke.
- Every phase ends with a runnable validation command before the next phase.

## Guiding decisions / no-refactor rule

- The wire contract above is **fixed now**; later phases implement against it.
- The editor is **transient and one-shot**: each `open_editor` registers a
  fresh handler that is consumed on close.
- No relationship to annotations — the handler decides what the text means.
- Unicode glyphs (✓/✕) for keep/discard; no icon-font dependency.

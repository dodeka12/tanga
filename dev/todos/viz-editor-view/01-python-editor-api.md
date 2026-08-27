# Phase 1 — Python editor API

## Goal

Expose `open_editor` on `Visualizer`, register the `editor_closed` message, and
dispatch it to the user's handler.

## Steps

- [x] **1.1 — `visualizer.py`: handler storage**
  - Add `self._editor_close_handlers: dict[str, Any] = {}` in `__init__`.

- [x] **1.2 — `visualizer.py`: `open_editor`**
  - `open_editor(cid, *, label="", value="", on_close=None) -> str`:
    register `on_close` in `_editor_close_handlers[cid]`; push `editor_define`
    (async, mirroring the banner `banner_define` push); return `cid`.

- [x] **1.3 — `visualizer.py`: `_dispatch_control_event`**
  - Add an `editor_closed` branch: read `id`/`text`; look up the handler;
    `await handler(text, event)` (try/except + log); pop the handler.

- [x] **1.4 — `server.py`: routing**
  - Add `"editor_closed"` to the control message-type tuple.

- [x] **1.5 — Unit tests (`test_editor.py`)**
  - `open_editor("e", on_close=cb)` registers `cb` and pushes `editor_define`.
  - Dispatch `editor_closed {id:"e", text:"x"}` → `cb("x", event)` and the
    handler is unregistered.
  - Dispatch `editor_closed {id:"e", text:None}` → `cb(None, event)` (discard).

- [x] **1.6 — Validate**
  - `uv run pytest py/tests/viz/test_editor.py py/tests/viz/test_banner.py -q`.

## Validation

`uv run pytest py/tests/viz/test_editor.py py/tests/viz/test_banner.py -q`

## Notes

- Mirrors `banner_closed` (dedicated message + lookup dict + try/except log).
- The editor is one-shot: the handler is popped after it runs.

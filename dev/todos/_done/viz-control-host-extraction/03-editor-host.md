# Phase 3 — Extract `EditorHost`

## Goal

Move the one-shot text editor out of `Visualizer` into a small `EditorHost`.

## Files

- Edit: `py/pytanga/viz/_hosts.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_editor.py` (add a direct `EditorHost` unit test)

## Steps

- [x] **3.1 — `EditorHost(OverlayHost)`**
  - Move `open_editor` and `_push_editor_define` into it.
  - Add `async _on_close(target, value, event)` (the `editor_closed` branch:
    lookup `(target, "close")`, unregister, await; `value` = editor text or
    `None`).

- [x] **3.2 — Wire `Visualizer`**
  - `__init__`: `self._editor_host = EditorHost(runtime)`.
  - `open_editor` becomes a one-line forwarder.
  - Route the `editor_closed` branch of `_dispatch_control_event` to
    `self._editor_host._on_close(...)`.

- [x] **3.3 — Tests**
  - `test_editor.py` passes unchanged; add a direct `EditorHost` test
    (open → push → close-discard / close-keep).

## Validation

`uv run pytest py/tests/viz/test_editor.py -q`

## Notes

- Keep `EditorHost` small and one-shot; the plan records it may grow a richer
  message contract later (e.g. save-as / cancel).

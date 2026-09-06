# Phase 2 — Extract `DialogHost`

## Goal

Move the dialog lifecycle out of `Visualizer` into a `DialogHost`, mirroring the
banner extraction.

## Files

- Edit: `py/pytanga/viz/_hosts.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_file_chooser.py` (or `test_banner.py`-style dialog test)

## Steps

- [x] **2.1 — `DialogHost(OverlayHost)`**
  - Move `_dialogs`, `_dialog_counter`, `_next_dialog_id`, `_register_dialog`,
    `_unregister_dialog`, `_find_dialog`, `show_dialog`, `remove_dialog`,
    `clear_dialogs`, `_push_dialog*`, and the `*_async` variants into it.
  - Add `async _on_accept(target, value, event)` and `async _on_close(...)`
    (the `accept`/`close` branches today: lookup + unregister + await, and
    `remove_dialog` for `close`).

- [x] **2.2 — Wire `Visualizer`**
  - `__init__`: `self._dialog_host = DialogHost(runtime)`.
  - Forward `show_dialog`/`remove_dialog`/`clear_dialogs` (+ async) to the host.
  - Keep `viz._dialogs` / `_dialog_counter` as delegating properties.
  - Route the `accept` and dialog `close` branches of `_dispatch_control_event`
    to `self._dialog_host._on_accept(...)` / `._on_close(...)`.

- [x] **2.3 — Tests**
  - Existing dialog/file-chooser tests pass unchanged; add a direct `DialogHost`
    test (register → push → accept/close → unregister).

## Validation

`uv run pytest py/tests/viz/test_file_chooser.py py/tests/viz/test_banner.py -q`

## Notes

- `_register_dialog` already calls `self._register_view_handlers(dialog.content)`;
  after this phase it calls `runtime.registry`-backed registration (delegated
  from `ControlHost` once phase 4 lands, or kept as a small forwarder meanwhile).

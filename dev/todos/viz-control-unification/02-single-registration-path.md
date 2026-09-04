# Phase 2 — One `ControlView`→registry registration path

## Goal

Collapse handler registration onto a single helper that, given a `ControlView`,
registers every handler it carries (change, click, press, release, and the table
events) into the shared `ControlHandlerRegistry`. The layout walk in
`_register_view_handlers` becomes a thin iteration over that helper.

## Files

- Edit: `py/pytanga/viz/visualizer.py`

## Steps

- [x] **2.1 — Extend `_register_view_handlers` event coverage (`visualizer.py`)**
  - Register `on_press` → `event="press"` and `on_release` → `event="release"`
    when present on the view.
  - Change the `on_change`/`on_click` `elif` to independent `if`s so a view
    carrying both registers both.

- [x] **2.2 — Extract `_register_control_view_handlers(view)`**
  - Move the per-view handler-gathering loop into a helper
    `_register_control_view_handlers(view) -> bool` that returns `True` if at
    least one handler was registered.
  - Reimplement `_register_view_handlers` to call it per control view and keep
    returning the set of ids that had handlers.

## Validation

```
uv run pytest py/tests/viz/test_layout_api.py py/tests/viz/test_banner.py -q
```

## Notes

- This helper is reused by the `add_*` facade in Phase 3, so the panel and view
  paths register through identical code.
- `_dispatch_control_event` already handles `control:press` / `control:release`
  (`visualizer.py`), and the frontend slider already emits them — this phase only
  wires the registration.

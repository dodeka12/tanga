# Phase 1 — Change-event enrichment

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (`ControlEvent`,
> `ControlHandler`, the `(id, event)` registry).  This only adds fields to
> `ControlEvent` (anticipated by its docstring) and a per-field handler on
> `ControlUI`; no architecture change.

## Goal

Expose the changed field to `on_change` and let each field carry its own handler.

## Files

- **Edit** `py/pytanga/viz/_controls.py` — add `key`/`value` to `ControlEvent`.
- **Edit** `py/pytanga/viz/_params_ui.py` — add `on_change` to `ControlUI` (and to
  the `_SHARED_UI_FIELDS` skip set so `_ui_kwargs` doesn't forward it).
- **Edit** `py/pytanga/viz/views/params_view.py` — set `event.key`/`event.value` in
  `_make_handler`; prefer `ui.on_change` over the shared handler in `_build_child`.
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **1.1 — `ControlEvent.key`/`value`**
  - Add `key: str | None = None` and `value: Any = None` to the `ControlEvent`
    dataclass in `_controls.py`.
- [x] **1.2 — `ControlUI.on_change`**
  - Add `on_change: ControlHandler | None = None` to the `ControlUI` base in
    `_params_ui.py`; add `"on_change"` to `_SHARED_UI_FIELDS` so `_ui_kwargs`
    does not forward it to the control constructor.
- [x] **1.3 — wire it through `ParamsView`**
  - In `_make_handler`, set `event.key = key` and `event.value = value` (the
    closure already has both) before calling the handler.
  - `_make_handler(key, field_handler)` / `_make_click_handler(key, field_handler)`
    store the value, then call the per-field handler (when set) with
    `(value, event)`, else the shared `self.on_change` with `(state, event)`.
- [x] **1.4 — tests**
  - Assert `on_change` receives `event.key`/`event.value`; assert a per-field
    handler is called for its field and the shared handler for the others.

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py -q
```

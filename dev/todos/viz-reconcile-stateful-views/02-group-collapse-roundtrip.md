# Phase 2 — Group collapse round-trip (`on_toggle` + `set_collapsed`)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `GroupView.collapsed` a backend-authoritative state: the user's
collapse/expand toggle reports to the backend (`control:group_toggle`), and the
backend can set it programmatically via `GroupView.set_collapsed(...)`, pushed as
`control_state` `{collapsed}`.  This is the documented "`GroupView` + `on_toggle`"
pattern (a `View` container with a control-like field), **not** a `ControlView`
conversion.

## Files

- Edit: `py/pytanga/viz/views/group_view.py`
- Edit: `py/pytanga/viz/views/functions.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/tests/viz/test_views.py`
- Edit: `py/tests/viz/test_layout_api.py`

## Steps

- [x] **2.1 — `GroupView` model (`group_view.py`)**
  - Add `on_toggle: ControlHandler | None = None` to `__init__` and store
    `self.on_toggle`; add `self._push_state = None` slot.
  - Add `set_collapsed(collapsed: bool)` that sets `self.collapsed = bool(collapsed)`
    and, when `_push_state` is set, pushes `{"collapsed": self.collapsed}`
    (mirrors `ControlView.set_visible`).

- [x] **2.2 — Group iteration + registration (`functions.py`, `_layout.py`)**
  - Add `iter_group_views(root)` (yield every `GroupView` in the tree, recursing
    `children` and `overlay`, like `iter_control_views`).
  - In `LayoutHost.register()`, also walk `iter_group_views`: set
    `view._push_state = self._push_control_state`, and register the handler via
    `self._transport.register(view.id, view.on_toggle, event="toggle")` when
    `view.on_toggle is not None` (mirror `Control.register_handlers`).

- [x] **2.3 — Dispatch (`_layout.py`)**
  - Add `resolve_group(cid)` (walk layouts for a `GroupView` with
    `view.id == cid`, mirroring `resolve_control`).
  - In `dispatch_control_event`'s `control:group_toggle` branch, resolve the
    group and set `group.collapsed = bool(value)` **before**
    `_fire(cid, "toggle", value, event)`, so the backend model stays authoritative
    even when no `on_toggle` handler is registered.

- [x] **2.4 — Frontend emit (`group-view.js`)**
  - In the toggle button's click handler, after `this.setCollapsed(!this.collapsed)`,
    call `sendControlEvent('control:group_toggle', this.groupId, this.collapsed)`.
  - Keep `setCollapsed(collapsed)` itself silent (no event) so a backend-initiated
    `control_state {collapsed}` applies without echoing.

- [x] **2.5 — Frontend apply (`viewer.js`)**
  - In the `control_state` branch (next to the existing `visible` handling), add:
    `if (msg.collapsed !== undefined) { const g = _viewRegistry.get(msg.id); if (g && typeof g.setCollapsed === 'function') g.setCollapsed(!!msg.collapsed); }`.

- [x] **2.6 — Tests**
  - `test_views.py`: `GroupView.set_collapsed` mutates and pushes via a stubbed
    `_push_state`; `on_toggle` is registered under `(id, "toggle")` only when set.
  - `test_layout_api.py`: dispatching `control:group_toggle` updates
    `group.collapsed` and fires the registered `on_toggle`.

## Validation

```
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_layout_api.py -q
node js/dev/tests/check-syntax.mjs
```

## Notes

- `control_state` already carries `enabled`/`visible`/`selected`/`min`/`max`/
  `step`; this phase adds `collapsed` for `GroupView` (resolved via
  `viewer.js`'s `_viewRegistry` lookup, not `_controlRegistry`).
- `sendControlEvent('control:group_toggle', …)` already maps through
  `controls-panel.js` `_CONTROL_EVENTS`; no new frontend message envelope.
- Frontend `setCollapsed` is idempotent (early-returns when unchanged), so a
  programmatic echo is harmless.

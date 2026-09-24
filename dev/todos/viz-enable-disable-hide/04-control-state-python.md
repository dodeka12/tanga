# Phase 4 — Control state (Python model + push)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add `enabled`/`visible` to the `Control` model, let `ControlView` set them at
runtime, and push a granular `control_state` message (no `view_layout` re-push).

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views/control_view.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_controls.py`
- Edit: `py/tests/viz/test_views.py`
- Edit: `py/tests/viz/test_layout_api.py`

## Steps

- [x] **4.1 — `Control.enabled` / `Control.visible` (`_controls.py`)**
  - Add `enabled: bool = True` and `visible: bool = True` to the `Control` base
    dataclass (after `kind`).
  - In `serialize()`, emit `"enabled": False` / `"visible": False` only when
    non-default.

- [x] **4.2 — `ControlView` setters (`control_view.py`)**
  - Init `self._push_state = None` next to `self._push`.
  - Add `set_enabled`/`set_visible` (mutate `self.control`, call
    `self._push_state(self.id, {...})` when set) plus `enable`/`disable`/
    `show`/`hide` sugar.

- [x] **4.3 — Push + resolve (`_layout.py`)**
  - Add `_push_control_state(cid, state)` sending
    `{"type": "control_state", "id": cid, **state}`.
  - In `register()`, set `view._push_state = self._push_control_state` next to
    `view._push`.
  - Add `set_control_enabled(cid, enabled)` / `set_control_visible(cid,
    visible)` that `resolve_control(cid)`, mutate, and push (no-op when
    unresolved).

- [x] **4.4 — Visualizer forwarders (`visualizer.py`)**
  - `set_control_enabled` / `set_control_visible` → `self._layout.*`.

- [x] **4.5 — Tests**
  - Serialization (omitted when default, present when `False`); `ControlView`
    setters push `control_state` via a stub `_push_state`; `register()` injects
    `_push_state`; `set_control_enabled/visible` mutate + push.

## Validation

```bash
uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_views.py py/tests/viz/test_layout_api.py -q
```

## Notes

- `ControlView._serialize` already merges `control.serialize()`, so
  `enabled`/`visible` reach the initial layout with no extra change.

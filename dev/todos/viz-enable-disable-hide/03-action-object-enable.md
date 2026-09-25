# Phase 3 — Action-object enable/disable

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a master enable/disable switch on `ActSceneObject` that stops all capture
(hover/drag/click/scroll) via the existing `InteractionConfig.enabled` and the
existing `interaction` aspect — no new wire aspect.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_active.py`

## Steps

- [x] **3.1 — Master `_enabled` flag (`_active.py`)**
  - Add `self._enabled = True` in `ActSceneObject.__init__`.

- [x] **3.2 — Force `enabled` in `_register_interaction`**
  - In `_register_interaction`, after `cfg = self.interaction_config`, set
    `cfg.enabled = self._enabled` before `set_interaction`.

- [x] **3.3 — Public methods**
  - `set_enabled(self, enabled: bool)` → `self._enabled = enabled;
    self.refresh_interaction()`.
  - `enable()` / `disable()` sugar.

- [x] **3.4 — Tests (`test_active.py`)**
  - `set_enabled(False)` produces an `InteractionConfig` with `enabled=False`
    and the original triggers retained; `enable()` restores it.

## Validation

```bash
uv run pytest py/tests/viz/test_active.py -q
```

## Notes

- `Scene.set_interaction` already marks `"interaction"` dirty, and `flush()`
  emits the `interaction` patch the frontend applies by re-registering the
  object with `enabled=False`.

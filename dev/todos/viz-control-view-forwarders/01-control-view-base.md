# Phase 1 — `ControlView` base (delete `__getattr__`, add shared forwarders)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Delete `ControlView.__getattr__` and add the shared, universally-typed
forwarders on the base, so `view.enabled` / `view.visible` / `view.selected`
and `view.get_value()` are explicit and type-checked.

## Files

- Edit: `py/pytanga/viz/views/control_view.py`

## Steps

- [ ] **1.1 — delete `__getattr__` (`control_view.py`)**
  - Remove `ControlView.__getattr__` entirely.

- [ ] **1.2 — typed `enabled` / `visible` / `selected` reads**
  - Add read-only `@property` `enabled -> bool`, `visible -> bool`,
    `selected -> bool` returning `self.control.<field>`.

- [ ] **1.3 — typed `get_value`**
  - Add `def get_value(self) -> Any: return self.control.get_value()` on the
    base, mirroring the existing `set_value(self, value: Any)`.  `value` types
    differ per kind, so the base return is `Any` (the documented dynamic-value
    surface); concrete views override to narrow (e.g. `TableView` already
    returns `dict[str, Any]`).

## Validation

```bash
uv run ty check && uv run ruff check . && uv run pytest py/tests/viz -q
```

## Notes

- `set_value` / `set_enabled` / `set_visible` / `set_selected` and
  `enable` / `disable` / `show` / `hide` are already explicit; only the reads
  were flowing through `__getattr__`.

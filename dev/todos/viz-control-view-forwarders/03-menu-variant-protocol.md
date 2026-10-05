# Phase 3 — Menu variant `Protocol`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace the `getattr`/`hasattr` duck-typing in `menu_view._apply_menu_variant`
with a structural `Protocol` (or `isinstance` union), and re-verify the
binding-boundary `cast` in `functions.py::control_to_view`.

## Files

- Edit: `py/pytanga/viz/views/menu_view.py`
- Edit: `py/pytanga/viz/views/functions.py`

## Steps

- [ ] **3.1 — `VariantControl` Protocol (`menu_view.py`)**
  - Add `class VariantControl(Protocol): variant: EControlVariant` (or an
    `isinstance` union over `Slider` / `Button` / `Checkbox` / `Dropdown`).
  - Rewrite `_apply_menu_variant` to recurse with `isinstance(child,
    ControlView)` and set `child.control.variant = EControlVariant.MENU` only
    when `isinstance(child.control, VariantControl)`.

- [ ] **3.2 — re-verify `control_to_view` cast (`functions.py`)**
  - Confirm `cast("Any", view).control = ctrl` is still the only cast (binding
    boundary) and its comment stays accurate after the base/forwarder changes.

## Validation

```bash
uv run ty check && uv run ruff check . && uv run pytest py/tests/viz -q
```

## Notes

- `menu_view.py` currently imports only `EControlVariant` from `.._controls`;
  add the `ControlView` import from `.control_view` and the
  `Protocol`/control imports (or place the protocol in a shared typing module).

# Phase 2 — Toolbar variant `Protocol`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Rewrite `toolbar_view._apply_toolbar_variant` to use the shared
`VariantControl` `Protocol` and `ControlView` instead of `getattr`/`hasattr`,
matching the `menu_view._apply_menu_variant` change already in place.

## Files

- Edit: `py/pytanga/viz/views/toolbar_view.py`

## Steps

- [x] **2.1 — typed `_apply_toolbar_variant`**
  - Import `ControlView` from `.control_view` and `VariantControl` from
    `.._controls`.
  - Replace the body:
    ```python
    ctrl = getattr(child, "control", None)
    if ctrl is not None and hasattr(ctrl, "variant"):
        ctrl.variant = EControlVariant.TOOLBAR
    ```
    with:
    ```python
    if isinstance(child, ControlView):
        ctrl = child.control
        if isinstance(ctrl, VariantControl):
            ctrl.variant = EControlVariant.TOOLBAR
    ```
  - Keep the `MenuView` early-`continue` and the recursive call unchanged.

## Validation

```bash
uv run ty check && uv run ruff check . && uv run pytest py/tests/viz -q
```

## Notes

- This is the direct sibling of `menu_view._apply_menu_variant`; reuse the same
  `VariantControl` (now in `_controls.py`) — do not re-declare it.
- `EControlVariant` is already imported in `toolbar_view.py`; only the two new
  imports are needed.

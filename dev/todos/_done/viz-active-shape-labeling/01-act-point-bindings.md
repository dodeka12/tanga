# Phase 1 — `ActPoint` drag/click bindings

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If this
> work introduces or changes architecture, update the developer docs.

## Goal

Let an `ActPoint` handle react to modifier/button-specific interactions by
exposing the base class's `drag_bindings` / `click_bindings` through its
constructor and emitting the matching triggers.  This is the enabler for
`ActPolygon`'s Ctrl+right-click vertex delete (phase 4).  No behaviour change
for existing `ActPoint` usage.

## Files

- Edit: `py/pytanga/viz/_active.py` (`ActPoint.__init__`, `ActPoint.interaction_config`)
- Edit: `py/tests/viz/test_active.py` (new tests)

## Steps

- [x] **1.1 — Add constructor params and forward them.**
  - Add `drag_bindings: list[DragBinding[ActSceneObject]] | None = None` and
    `click_bindings: list[ClickBinding[ActSceneObject]] | None = None` to
    `ActPoint.__init__`, and pass them to `super().__init__(...)`.
  - Update the class docstring `Args:` section.
- [x] **1.2 — Emit triggers for the bindings.**
  - In `ActPoint.interaction_config`, after the existing drag/click triggers,
    append one `InteractionTrigger(DRAG, binding.button, binding.modifiers,
    drag_mode=mode_or_view_plane)` per enabled `_drag_bindings` entry, and one
    `InteractionTrigger(CLICK, binding.button, binding.modifiers)` per enabled
    `_click_bindings` entry — mirroring `ActImagePlane.interaction_config`.
  - Use the point's resolved drag mode for binding drag triggers
    (`XY_PLANE` in 2D, else `VIEW_PLANE`), so modifier drags stay in-plane.
- [x] **1.3 — Tests.**
  - Add `py/tests/viz/test_active.py` cases: a `DragBinding(LEFT, h, ModifierKey.CTRL)`
    produces a `DRAG` trigger with `modifiers == {"ctrl"}`; a
    `ClickBinding(MouseButton.RIGHT, h, ModifierKey.CTRL)` produces a `CLICK`
    trigger with `mouse_button == RIGHT` and `modifiers == {"ctrl"}`.
  - Assert existing `ActPoint` usage (no bindings) is unchanged.

## Validation

```
uv run pytest py/tests/viz/test_active.py -q
```

## Notes

- `_resolve_drag_handler` / `_resolve_click_handler` already pick the
  most-specific binding, so a Ctrl binding wins over the general `handler`.
- The existing catch-all XY/VIEW drag trigger fires regardless of modifiers, so
  `ActPolygon`'s Ctrl+drag insert (phase 4) can be handled by branching on
  `event.modifiers` in the general `handler` — it does not need `drag_bindings`.

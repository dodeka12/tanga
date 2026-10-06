# Phase 1 — `ActPoint.set_drag_modifiers` primitive

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> This stays inside the existing `ActSceneObject` interaction-config recipe; no
> architecture change.

## Goal

Let a single `ActPoint` require modifier keys (all held) for its drag, so a host
can declare "Shift+drag edits this point" declaratively.  Empty modifiers = the
current default (always draggable).

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_active.py`

## Steps

- [x] **1.1 — Store the requirement on `ActPoint`.**
  - In `ActPoint.__init__`, add
    `self._required_drag_modifiers: frozenset[ModifierKey] = frozenset()`.
- [x] **1.2 — Add `set_drag_modifiers`.**
  - Add `def set_drag_modifiers(self, *modifiers: ModifierKey) -> None:` that sets
    `self._required_drag_modifiers = frozenset(modifiers)` and calls
    `self.refresh_interaction()`.
- [x] **1.3 — Apply the requirement in `interaction_config`.**
  - In the single-trigger branch (the `else` where `mode is not None`), add
    `modifiers=self._required_drag_modifiers` to the lone
    `InteractionTrigger(event_type=InteractionEventType.DRAG, mouse_button=MouseButton.LEFT, drag_mode=mode)`.
    Leave the four-trigger `_default_drag_triggers(...)` branch unchanged.
- [x] **1.4 — Tests.**
  - In `test_active.py`: default `interaction_config` keeps an unmodified
    single-trigger drag (`modifiers == frozenset()`); after
    `set_drag_modifiers(ModifierKey.SHIFT)` the trigger carries
    `modifiers == frozenset({ModifierKey.SHIFT})`; after `set_drag_modifiers()`
    it resets to empty.

## Validation

`uv run pytest py/tests/viz/test_active.py -q`

## Notes

- Composite handles always construct `ActPoint(..., drag_mode=DragMode.XY_PLANE)`,
  so they always take the single-trigger branch this phase targets.

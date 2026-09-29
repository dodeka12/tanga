# Phase 2 — Shared handle base + `ActRectangle2D` body `on_click`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If this
> work introduces or changes architecture, update the developer docs.

## Goal

De-duplicate the "body + `ActPoint` handles" bookkeeping into a private
`_ActWithHandles(ActSceneObject)` base, refactor `ActRectangle2D` onto it with
no behaviour change, then add body `on_click` so a composite can be selected by
clicking its body.

## Files

- Edit: `py/pytanga/viz/_active.py` (new `_ActWithHandles`; refactor + extend `ActRectangle2D`)
- Edit: `py/tests/viz/test_act_rectangle2d.py` (on_click tests)

## Steps

- [x] **2.1 — Add `_ActWithHandles` base.**
  - Define `_ActWithHandles(ActSceneObject)` holding `_handle_ids: list[str]`,
    a `_spawn_handle(handle_act, *, style=None, drag_handler=None,
    click_bindings=None, on_drag_start=None, on_drag_end=None) -> str` helper,
    `remove()` (removes handles + body), `clear()` alias, and
    `_remove_handles()`.
- [x] **2.2 — Refactor `ActRectangle2D` onto it.**
  - Inherit `_ActWithHandles`; move the existing `_handle_ids`, `remove()` and
    handle-spawn logic into the base without changing public API or geometry.
  - Run the existing tests to confirm no behaviour change.
- [x] **2.3 — Add body `on_click` to `ActRectangle2D`.**
  - Add `on_click: ActClickHandler | None = None`; forward to
    `super().__init__(..., on_click=on_click)`.
  - In `ActRectangle2D.interaction_config`, when `_on_click is not None` return
    `enabled=True` with a `CLICK` trigger (`mouse_button=LEFT`); otherwise keep
    the current `InteractionConfig(enabled=False, triggers=[])`.
- [x] **2.4 — Tests.**
  - `test_act_rectangle2d.py`: body config is disabled without `on_click`;
    with `on_click`, config is `enabled=True` and contains a `CLICK` trigger.

## Validation

```
uv run pytest py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_active.py -q
```

## Notes

- `ActSceneObject._register_interaction` already registers the CLICK handler when
  `_on_click` is set; this phase only surfaces the trigger + enabled flag.
- The body `drag_anchor` already returns the rectangle centre, so
  `_resolve_click_anchor` reports the centre — fine for selection.

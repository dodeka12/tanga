# Phase 6 — Keyboard facility (frontend, per-pane focus)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs (see phase 08).

## Goal

Add a per-pane `keydown` listener to `ThreeJsView` (per-pane focus), consume the
`scene_config.keyboard` list, and send `interaction:key` messages to the backend.

## Files

- Edit: `py/pytanga/viz/templates/views/three-view.js` (keydown listener + keyboard state)
- Edit: `py/pytanga/viz/templates/viewer.js` (reuse/generalize the key-matching helper, if shared)

## Steps

- [x] **6.1 — Per-pane keydown listener.**
  - In `ThreeJsView._initScene`, give the pane `this.el.tabIndex = 0`, focus it
    on `pointerdown` (so focus is implicit), and attach a `keydown` listener that
    calls a new `_handleKeyDown(event)`.
- [x] **6.2 — Consume `scene_config.keyboard`.**
  - In `_applySceneConfig`, store `this._keyBindings = config.keyboard || []`.
- [x] **6.3 — Match + send.**
  - `_handleKeyDown(event)`: guard editable targets
    (`INPUT`/`TEXTAREA`/`isContentEditable`) and `event.repeat`; match
    `event.key`/modifiers against `this._keyBindings` (reuse the matching logic
    already in `viewer.js` `_stopKeyMatches`, extracted/generalized if needed);
    on match `preventDefault()` and send
    `{ type: 'interaction:key', event_type: 'key', scene: this.sceneName,
       key: event.key, modifiers: [...], browser_id: this._browserId }`.
- [x] **6.4 — Cleanup.** Remove the listener in the pane's teardown path if one
  exists (mirror `InteractionController` lifetime).

## Validation

```
uv run pytest py/tests/viz -q
```

(Manual: run `py/examples/viz/image/rectangle_labeling.py` after phase 7 and
press Delete/Escape with the pane focused — the backend handler fires.)

## Notes

- No automated JS test harness in this repo; the frontend phase is gated by the
  backend regression suite plus a manual browser check.
- Keep the existing global `animation_stop` key binding (`viewer.js`) untouched.

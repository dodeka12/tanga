# Phase 2 — Control range (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Apply server-driven `min` / `max` / `step` from `control_state` to the rendered
slider and value-edit DOM, without re-pushing `view_layout`.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/controls/value-edit.js`

## Steps

- [x] **2.1 — range support in `applyControlStateToElement` (`controls-panel.js`)**
  - When `state.min` / `state.max` / `state.step` is present, target
    `wrapper.querySelector('input[type="range"]')`; set its `min`/`max`/`step`
    (the browser auto-clamps `value`), then sync the `.tanga-value` readout to
    the clamped `input.value`.  This covers the slider.

- [x] **2.2 — per-entry `applyState` hook (`controls-panel.js`)**
  - In `applyControlState(id, state)`, call `entry.applyState(state)` when the
    registry entry defines it, else fall back to
    `applyControlStateToElement(entry.el, state)`.

- [x] **2.3 — value-edit `applyState` (`controls/value-edit.js`)**
  - Change the captured `min` / `max` / `step` to `let`; register
    `applyState(state)` that reassigns `min`/`max`/`step`, re-clamps the current
    `value` into the new range, re-renders `input.value`, then calls
    `applyControlStateToElement(wrapper, state)` for `enabled`/`visible`/
    `selected`.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py --check
```

## Notes

- `value-edit` has no native range attributes; its `min`/`max`/`step` live in
  the factory closures, hence the dedicated `applyState`.
- The slider reuses 2.1's generic range handling and needs no factory change.

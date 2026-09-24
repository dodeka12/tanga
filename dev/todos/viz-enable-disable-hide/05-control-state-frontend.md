# Phase 5 — Control state (frontend + theme)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Apply `enabled`/`visible` to rendered controls (initial + runtime) and grey out
disabled controls with themeable CSS.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/controls/*.js` (11 factories)
- Edit: `py/pytanga/viz/templates/themes/base.css`

## Steps

- [x] **5.1 — Shared state applier (`controls-panel.js`)**
  - Add `applyControlStateToElement(wrapper, state)` that toggles
    `.tanga-control-disabled`, sets `disabled` on
    `wrapper.querySelectorAll('input, select, textarea, button')`, and sets
    `wrapper.style.display`.
  - Add `applyControlState(id, state)` that looks up `_controlRegistry[id].el`.

- [x] **5.2 — Route `control_state` (`viewer.js`)**
  - Add `if (msg.type === 'control_state') { applyControlState(msg.id, msg); return; }`
    next to the `control_update` branch.

- [x] **5.3 — Factory wiring (`controls/*.js`)**
  - In each `create<Kind>`: store `el: wrapper` in the `registerControl` entry,
    call `applyControlStateToElement(wrapper, ctrl)` once for initial state, and
    add `applyState: (s) => applyControlStateToElement(wrapper, s)`.

- [x] **5.4 — Themeable disabled styling (`base.css`)**
  - Add `--tanga-disabled-opacity: 0.45` and `--tanga-disabled-fg:
    var(--tanga-fg-muted)` to `:root`.
  - Add `.tanga-control-disabled { opacity: var(--tanga-disabled-opacity);
    pointer-events: none; }`.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py --check
```

## Notes

- Themes override the tokens in their `tokens.css` / `overrides/*.css`.

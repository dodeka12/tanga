# Phase 3 — Menu auto-close

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Close a menu (and its ancestor menus) automatically after an option is chosen:
a button `click` or a dropdown `change` on a `.tanga-menu-item`.

## Files

- Edit: `py/pytanga/viz/templates/views/menu-view.js`

## Steps

- [x] **3.1 — `_closeTree()` (`menu-view.js`)**
  - Add a private helper that walks `_parentMenu` up to the root and calls
    `root.close()` (a bar's `close()` already cascades to its sub-menus).

- [x] **3.2 — delegated option listener (`menu-view.js`)**
  - In the constructor, add a delegated listener on `this.el` that calls
    `this._closeTree()` when the event target is inside a `.tanga-menu-item`:
    - `click` on `button.tanga-action-button` → close;
    - `change` on `select` → close.
  - Skip when the target is inside `.tanga-menu-trigger` (sub-menu toggles) or
    is an `input[type="range"]` (sliders stay open while dragging).

- [x] **3.3 — cleanup (`menu-view.js`)**
  - Remove the listener in `destroy()` next to the existing outside-click /
    Escape teardown.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py --check
```

## Notes

- The option's own `control:click` / `control:change` send still fires (the
  delegated listener is a separate bubble-phase handler on an ancestor), so the
  server handler runs independently of the close.

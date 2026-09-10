# Phase 1 — Export the shared debounce helper

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the shared input-debounce helper importable by the
`controls/text-field.js` / `controls/text-area.js` / `controls/color-picker.js`
factories created in Phase 2.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`

## Steps

- [x] **1.1 — Rename and export `_attachDebouncedChange`**
  - Rename `_attachDebouncedChange` to `attachDebouncedChange` and mark it
    `export function attachDebouncedChange(...)` (same body).
  - Update the three in-file call sites (`createTextField`, `createTextArea`,
    `createColorPicker`) to call `attachDebouncedChange`.

## Validation

`node --check py/pytanga/viz/templates/controls-panel.js`

## Notes

- The three call sites are removed in Phase 4; keeping them consistent here is
  just so the core stays self-contained until then.

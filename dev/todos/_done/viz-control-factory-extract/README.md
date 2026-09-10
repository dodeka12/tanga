# Viz control factory extraction — Overview

**Created:** 2026-09-07 | **Status:** Done | **Branch:** `fix/misc`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Move the per-control DOM factories out of
`py/pytanga/viz/templates/controls-panel.js` into one module per control under
`py/pytanga/viz/templates/controls/` (analogous to the already-split
`controls/table.js`), leaving `controls-panel.js` as the shared core (registry,
event dispatch, icons, helpers). Delete the orphaned `createFileChooser`.

## Architecture (short)

No wire format, control model, or event envelope changes — this is a pure
frontend module re-organization. The fixed up-front contract is the module
layout:

- `controls-panel.js` keeps the shared core only:
  - registry: `registerControl`, `applyControlValue`, `applyEnumOptions`,
    `forgetControl`
  - icons: `createIconElement`
  - helpers: `applyTooltip`, `attachDebouncedChange` (renamed from the private
    `_attachDebouncedChange`)
  - event dispatch: `sendControlEvent`, `resolveUndoRedoAction`,
    `throttledSend`, `throttledFlush`
- Each `create<X>(ctrl)` moves to `controls/<x>.js`, imports its shared helpers
  from `../controls-panel.js` (markdown also imports `sendLog` from
  `../events.js`), and registers via `registerControl(id, { owner, kind, apply })`
  instead of the former direct `_controlRegistry[id] = …`.
- The layout view `views/<x>-view.js` imports `create<X>` from
  `../controls/<x>.js`; `banner-view.js` imports the banner-able factories from
  the same modules.

| Factory | New module | Layout view (rewired) |
|---------|-----------|----------------------|
| `createSlider` | `controls/slider.js` | `views/slider-view.js` |
| `createDropdown` | `controls/dropdown.js` | `views/dropdown-view.js` |
| `createButton` | `controls/button.js` | `views/button-view.js` |
| `createTextField` | `controls/text-field.js` | `views/text-field-view.js` |
| `createTextArea` | `controls/text-area.js` | `views/text-area-view.js` |
| `createLabel` | `controls/label.js` | `views/label-view.js` |
| `createMarkdown` | `controls/markdown.js` | `views/markdown-view.js` |
| `createColorPicker` | `controls/color-picker.js` | `views/color-picker-view.js` |
| `createCheckbox` | `controls/checkbox.js` | `views/checkbox-view.js` |
| `createValueEdit` | `controls/value-edit.js` | `views/value-edit-view.js` |
| `createFileChooser` | _(deleted — orphaned)_ | — |

## Decisions (confirmed)

- Factories go to `controls/<x>.js` (not into the view classes), matching the
  existing `controls/table.js` pattern.
- `createFileChooser` is orphaned (only `control-registry.test.mjs` referenced
  it); remove it rather than relocate it.
- `controls-panel.js` remains the single shared core (registry + event dispatch
  + icons + helpers) that all `controls/*.js` modules import.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-shared-debounce-helper.md](./01-shared-debounce-helper.md) | Export `attachDebouncedChange` from the core. |
| 2 | [02-extract-control-factories.md](./02-extract-control-factories.md) | Create `controls/<x>.js` and rewire each layout view. |
| 3 | [03-rewire-banner-and-tests.md](./03-rewire-banner-and-tests.md) | Rewire `banner-view.js` + unit tests to the new modules. |
| 4 | [04-remove-dead-factories.md](./04-remove-dead-factories.md) | Delete the factories + orphaned `createFileChooser` from the core. |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Update architecture docs + changelog. |

## Testing as you go

- `node --check <file>` — syntax check each touched JS file.
- `node --test 'dev/src/js-tests/*.test.mjs'` — the JS unit tests (Node).
- `uv run mkdocs build --strict` — docs build (Phase 5).

## Non-goals

- No Python control-model / wire-format / event-envelope changes.
- No changes to `controls/table.js` (already split) beyond its unchanged import
  of shared helpers from `controls-panel.js`.
- No user-visible behavior or CSS changes.
- Not deleting any factory other than the orphaned `createFileChooser`.

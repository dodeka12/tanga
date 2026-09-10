# Phase 3 — Rewire `banner-view.js` and unit tests

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Point every remaining importer (banner + tests) at the new `controls/*.js`
modules so `controls-panel.js` can drop its factories in Phase 4.

## Files

- Edit: `py/pytanga/viz/templates/views/banner-view.js`
- Edit: `dev/src/js-tests/toolbar-chrome.test.mjs`
- Edit: `dev/src/js-tests/markdown-view.test.mjs`

## Steps

- [x] **3.1 — Rewire `banner-view.js`**
  - Replace the single
    `import { createSlider, createButton, createDropdown, createTextField, createTextArea, createColorPicker, createCheckbox } from '../controls-panel.js'`
    with seven imports, one per `../controls/<x>.js` module:
    `slider.js`, `dropdown.js`, `button.js`, `text-field.js`, `text-area.js`,
    `color-picker.js`, `checkbox.js`.

- [x] **3.2 — Rewire `toolbar-chrome.test.mjs`**
  - Import `createCheckbox` from `controls/checkbox.js`, `createDropdown` from
    `controls/dropdown.js`, `createSlider` from `controls/slider.js`.

- [x] **3.3 — Rewire `markdown-view.test.mjs`**
  - Import `createMarkdown` from `controls/markdown.js`.

## Validation

`node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- `controls-panel.js` still exports the factories here; Phase 4 removes them.

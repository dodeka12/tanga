# Phase 4 — Remove the dead factories and orphaned `createFileChooser`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Strip `controls-panel.js` down to the shared core (registry, event dispatch,
icons, helpers) and delete the orphaned `createFileChooser`.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `dev/src/js-tests/control-registry.test.mjs`

## Steps

- [x] **4.1 — Stop using `createFileChooser` in `control-registry.test.mjs`**
  - Replace the `createFileChooser` import/uses with `createTextField` (imported
    from `controls/text-field.js`) so the test still registers two entries. Keep
    the `applyControlValue`/`forgetControl` assertions unchanged.

- [x] **4.2 — Delete the 10 factories and `_renderMarkdown` from `controls-panel.js`**
  - Remove `createSlider`, `createDropdown`, `createButton`, `createTextField`,
    `createTextArea`, `createLabel`, `createMarkdown`, `_renderMarkdown`,
    `createColorPicker`, `createCheckbox`, `createValueEdit`.

- [x] **4.3 — Delete `createFileChooser` from `controls-panel.js`**
  - Remove the function and its now-unused
    `import { openFileBrowser } from './file-browser.js'`.

- [x] **4.4 — Finalize the core**
  - Remove the now-unused `sendLog` from the `events.js` import (keep `sendEvent`).
  - Update the file header comment to describe the shared core (registry + event
    dispatch + icons + helpers) rather than "control factories".

## Validation

```
node --check py/pytanga/viz/templates/controls-panel.js
node --test 'dev/src/js-tests/*.test.mjs'
```

## Notes

- After this phase there must be no `create<X>`, `_controlRegistry[`,
  `_applyTooltip`, or `_attachDebouncedChange` references left in
  `controls-panel.js`.

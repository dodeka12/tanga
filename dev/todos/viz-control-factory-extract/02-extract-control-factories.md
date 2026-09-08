# Phase 2 — Extract control factories into `controls/*.js`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Create `templates/controls/<x>.js` for each of the 10 controls (moving the
factory body out of `controls-panel.js`) and rewire the matching layout view to
import from the new module. `controls-panel.js` still exports the factories in
this phase (transient duplication) so `banner-view.js` and the tests continue to
resolve until Phase 3.

## Files

- New: `py/pytanga/viz/templates/controls/slider.js`
- New: `py/pytanga/viz/templates/controls/dropdown.js`
- New: `py/pytanga/viz/templates/controls/button.js`
- New: `py/pytanga/viz/templates/controls/text-field.js`
- New: `py/pytanga/viz/templates/controls/text-area.js`
- New: `py/pytanga/viz/templates/controls/label.js`
- New: `py/pytanga/viz/templates/controls/markdown.js`
- New: `py/pytanga/viz/templates/controls/color-picker.js`
- New: `py/pytanga/viz/templates/controls/checkbox.js`
- New: `py/pytanga/viz/templates/controls/value-edit.js`
- Edit: `py/pytanga/viz/templates/views/<x>-view.js` (10 files, one per control)

## Steps

- [x] **2.1 — `createSlider` → `controls/slider.js`**
  - New `controls/slider.js`: move the factory body; import
    `registerControl, applyTooltip, sendControlEvent, throttledSend, throttledFlush`
    from `../controls-panel.js`; register via `registerControl(id, …)`.
  - Edit `views/slider-view.js`: import `createSlider` from `../controls/slider.js`.

- [x] **2.2 — `createDropdown` → `controls/dropdown.js`**
  - New `controls/dropdown.js`; import `registerControl, applyTooltip, sendControlEvent`.
  - Edit `views/dropdown-view.js` import.

- [x] **2.3 — `createButton` → `controls/button.js`**
  - New `controls/button.js`; import `applyTooltip, sendControlEvent, createIconElement`
    (no registry entry — buttons only send `control:click`).
  - Edit `views/button-view.js` import.

- [x] **2.4 — `createTextField` → `controls/text-field.js`**
  - New `controls/text-field.js`; import `registerControl, applyTooltip, attachDebouncedChange`.
  - Edit `views/text-field-view.js` import.

- [x] **2.5 — `createTextArea` → `controls/text-area.js`**
  - New `controls/text-area.js`; import `registerControl, applyTooltip, attachDebouncedChange`.
  - Edit `views/text-area-view.js` import.

- [x] **2.6 — `createLabel` → `controls/label.js`**
  - New `controls/label.js`; import `registerControl, applyTooltip`.
  - Edit `views/label-view.js` import.

- [x] **2.7 — `createMarkdown` → `controls/markdown.js`**
  - New `controls/markdown.js`: move `_renderMarkdown` (module-private) +
    `createMarkdown`; import `registerControl, applyTooltip` from
    `../controls-panel.js` and `sendLog` from `../events.js`. Update the
    `sendLog` `source` to `'controls/markdown.js'`.
  - Edit `views/markdown-view.js` import.

- [x] **2.8 — `createColorPicker` → `controls/color-picker.js`**
  - New `controls/color-picker.js`; import `registerControl, applyTooltip, attachDebouncedChange`.
  - Edit `views/color-picker-view.js` import.

- [x] **2.9 — `createCheckbox` → `controls/checkbox.js`**
  - New `controls/checkbox.js`; import `registerControl, applyTooltip, sendControlEvent`.
  - Edit `views/checkbox-view.js` import.

- [x] **2.10 — `createValueEdit` → `controls/value-edit.js`**
  - New `controls/value-edit.js`; import `registerControl, applyTooltip, sendControlEvent, createIconElement`.
  - Edit `views/value-edit-view.js` import.

## Validation

```
node --check py/pytanga/viz/templates/controls/slider.js
node --check py/pytanga/viz/templates/controls/dropdown.js
node --check py/pytanga/viz/templates/controls/button.js
node --check py/pytanga/viz/templates/controls/text-field.js
node --check py/pytanga/viz/templates/controls/text-area.js
node --check py/pytanga/viz/templates/controls/label.js
node --check py/pytanga/viz/templates/controls/markdown.js
node --check py/pytanga/viz/templates/controls/color-picker.js
node --check py/pytanga/viz/templates/controls/checkbox.js
node --check py/pytanga/viz/templates/controls/value-edit.js
node --test 'dev/src/js-tests/*.test.mjs'
```

## Notes

- Copy the factory bodies verbatim; only three mechanical changes apply:
  `_controlRegistry[id] = …` → `registerControl(id, …)`,
  `_applyTooltip(...)` → `applyTooltip(...)`, and
  `_attachDebouncedChange(...)` → `attachDebouncedChange(...)`.
- `createButton` does not register a control (no `registerControl` import).
- `_renderMarkdown` stays module-private inside `controls/markdown.js`.

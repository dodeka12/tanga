# Phase 4 — Frontend control factories

## Goal

Render the new controls, button icons/icon_only, and tooltips in
`controls-panel.js`, and teach `controls-attached.js` about the new kinds.

## Steps

- [x] **4.1 — Icon rendering (`controls-panel.js`)**
  - `createIconElement(iconId)`: split on first `:`, default family
    `material`; render `material` as `<span class="material-icons">name</span>`,
    `uc` as a literal-text `<span>`, unknown/bare as literal text.
  - `_ensureIconFont(family)`: lazily inject
    `<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">`
    once (by element id); no-op for `uc`.

- [x] **4.2 — `createButton`**
  - Render `icon` before the label when set; when `icon_only`, add the
    `tanga-icon-button` class and set
    `btn.title = ctrl.tooltip || ctrl.label || ctrl.id`.

- [x] **4.3 — New factories**
  - `createTextField` (`<input type="text">`, debounced `control:change`).
  - `createTextArea` (`<textarea rows>`, debounced `control:change`).
  - `createColorPicker` (`<input type="color">`, `control:change` hex string).
  - `createCheckbox` (`<input type="checkbox">`, `control:change` boolean).
  - Reuse the file-chooser debounce helper where applicable.

- [x] **4.4 — Tooltip helper**
  - `_applyTooltip(wrapper, ctrl)`: `wrapper.title = ctrl.tooltip` when set;
    call from every factory.

- [x] **4.5 — Dispatch + CSS**
  - Extend `_createControlElement` switch with `text`/`textarea`/`color`/`checkbox`.
  - CSS for `.material-icons`, `.tanga-icon-button`, text/color/checkbox/textarea.

- [x] **4.6 — `controls-attached.js`**
  - Extend the per-kind dispatch to the four new kinds (+ `file_chooser`, a
    current gap) by importing the new factories.

- [x] **4.7 — Validate**
  - Manual viewer smoke: a group with all four new controls + an
    icon/icon_only button.

## Validation

Manual viewer smoke test (no DOM harness) + `uv run pytest py/tests/viz -q`
for Python regression.

## Notes

- All new factories send through the existing `sendControlEvent` (and `_ws`),
  so the Python dispatch in `_dispatch_control_event` needs no change.

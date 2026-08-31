# Phase 4 — Frontend rename

## Goal

Apply the rename on the JS side so the browser reads `value` for every
control kind, in both the `controls_define` panel path and the `view_layout`
path.

## Steps

- [x] **4.1 — `templates/controls-panel.js` factories**
  - `createSlider`: read `ctrl.value` (rename local `defaultVal` → `ctrlValue`).
  - `createDropdown`: `opt === ctrl.value`.
  - `createColorPicker`: `input.value = ctrl.value || '#ffffff'`.
  - `createCheckbox`: `input.checked = !!ctrl.value`.

- [x] **4.2 — `templates/views/build.js`**
  - `default: node.default` → `value: node.value` (4 sites).

- [x] **4.3 — `templates/views/*-view.js`**
  - `slider-view.js`, `dropdown-view.js`, `checkbox-view.js`,
    `color-picker-view.js`: destructure/assign/pass `value` instead of
    `default` / `defaultValue`.

- [x] **4.4 — Smoke pages `dev/src/js-tests/`**
  - `group-view-smoke.html`, `control-group-view-smoke.html`,
    `control-view-smoke.html`: `default:` → `value:`.

- [x] **4.5 — Validate**
  - Manual viewer smoke (no DOM harness) + confirm the frontend version hash
    picks up the change (`test_frontend_version.py` unchanged).

## Validation

`uv run pytest py/tests/viz/test_frontend_version.py -q` (frontend hash
recomputed automatically) plus a manual viewer smoke.

## Notes

- `banner-view.js` and `controls-attached.js` reuse the same factories, so they
  are covered without direct edits.

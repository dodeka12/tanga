# Phase 4 — Frontend control views

## Goal

Each control is a `View` that renders one HTML control (reusing the existing
factories) and sends the existing `control:*` events.

## Steps

- [x] **4.1 — `templates/views/control-view.js` (base)**
  - `ControlView extends View`; constructor `{ id, label }`; sets `this.controlId = id`.
  - Exposes a `render()` hook returning the control DOM element (subclass fills it).

- [x] **4.2 — `slider-view.js` / `button-view.js` / `dropdown-view.js`**
  - `SliderView extends ControlView` with `{ id, label, min, max, step, default }`;
    `render()` → `createSlider({ id, label, min, max, step, default })`.
  - `ButtonView` → `createButton({ id, label })`.
  - `DropdownView` → `createDropdown({ id, label, options, default })`.
  - Mount the rendered element into `this.el` on `_onMounted()`.
  - Events: the factories already call `sendControlEvent(...)` (module-level `_ws`
    in `controls-panel.js`, set by `viewer.js` on connect) — no new plumbing.

- [x] **4.3 — Natural size**
  - Report a sensible preferred size (e.g. control default height/width) via
    `preferredWidth`/`preferredHeight`; keep min small so a stack can size to
    content.

- [x] **4.4 — Smoke**
  - `dev/src/js-tests/control-view-smoke.html`: build a `StackView` of one of
    each control; verify they render and (mock) emit `control:*`.

## Validation

`node --input-type=module --check` on the new files + browser smoke page.

# Phase 7 — Frontend control views parity

## Goal

Add JS view classes for the new controls and thread tooltip/button-icon so the
`view_layout` path renders identically to the `controls_define` path.

## Steps

- [x] **7.1 — New view classes (`templates/views/`)**
  - `text-field-view.js`, `text-area-view.js`, `color-picker-view.js`,
    `checkbox-view.js` — each extends `ControlView` and renders via the
    matching factory (reusing the factories from Phase 4).

- [x] **7.2 — `button-view.js`**
  - Accept `icon`/`icon_only` and pass to `createButton`.

- [x] **7.3 — Tooltip threading**
  - Each view constructor accepts `tooltip` and passes it to its factory.

- [x] **7.4 — `views/build.js`**
  - Import the new views and wire `node.type` → constructor, passing
    `tooltip`, and for button `icon`/`icon_only`.

- [x] **7.5 — Validate**
  - Manual viewer smoke: a `StackView`/`GroupView` layout with the new control
    views.

## Validation

Manual viewer smoke test + `uv run pytest py/tests/viz/test_views.py -q`.

## Notes

- Keep the JS view constructors 1:1 with the Python view serialization fields
  (mirror the existing `slider-view.js` pattern).

# Phase 8 — `ControlGroupView`

## Goal

Render a scene's control groups inside a `View` pane and report a natural
`minHeight` that grows/shrinks as controls are added/removed — demonstrating
the `constraintschange` reaction path end-to-end.

## Steps

- [x] **8.1 — `templates/views/control-group-view.js`**
  - `ControlGroupView extends View`; constructor `(sceneName, groupId)`.
  - `handleMessage` routes `controls_define`/`controls_clear` into this view's
    `el`; `_syncMinHeight` sets `minHeight` (content height) and emits
    `constraintschange`.

- [x] **8.2 — Minimal `controls-panel.js` refactor**
  - `handleControlsDefine(msg, targetEl)` now accepts an optional container;
    when given, panels stack normally inside it (no fixed positioning/toggle
    button). No behavior change for the single-scene path.

- [x] **8.3 — Browser smoke**
  - `dev/src/js-tests/control-group-view-smoke.html`: renders a `controls_define`
    message into a pane, logs `minHeight` + `constraintschange`, then clears
    (manual check; serve over HTTP).

- [x] **8.4 — Validate**
  - `node --input-type=module --check` on the two touched files (OK) +
    `uv run pytest py/tests/viz/test_controls.py -q` (10 passed).

## Validation

`uv run pytest py/tests/viz/test_controls.py -q` + `node --input-type=module --check`

## Notes

- This phase proves the "container reacts to a leaf's constraint change" path
  before the full multi-view bootstrap lands.

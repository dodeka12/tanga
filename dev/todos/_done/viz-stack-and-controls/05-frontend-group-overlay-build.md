# Phase 5 — Frontend `GroupView`, `SceneView` overlay, `build.js` mapping

## Goal

Materialize the new nodes into DOM: `GroupView` (titled stack), the `SceneView`
overlay layer, and update `build.js` (rename + new types) and routing.

## Steps

- [x] **5.1 — `templates/views/group-view.js` (rename `control-group-view.js`)**
  - `GroupView extends StackView`; constructor
    `{ title, direction = 'vertical', position = null, collapsed = false }`.
  - Render a title header (+ collapse toggle) above the flex children; apply
    panel chrome styling (reuse the existing `.tanga-control-panel` look or a new
    `.tanga-group` class).
  - No `sceneName`; remove the old `handleMessage`/`handleControlsDefine` logic.

- [x] **5.2 — `ThreeJsView` overlay**
  - Add `addOverlay(view)` / overlay children: an absolutely-positioned layer over
    the canvas (`position: absolute` within `this.el`), anchoring each child by
    its `position` (`top-left`/`top-right`/`bottom-left`/`bottom-right`) reusing
    the existing anchor logic from `controls-panel.js::_positionPanel`.

- [x] **5.3 — `build.js`**
  - Map `stack` → `StackView`, `group` → `GroupView`, `slider_view`/`button_view`/
    `dropdown_view` → the control views, and `scene_view` overlay `children` →
    `ThreeJsView.addOverlay`.
  - Drop the `control_group_view` mapping (renamed to `group`).
  - `collectSceneRoutes`: only `ThreeJsView` is scene-bound now (control views and
    `GroupView` carry no scene); remove the `ControlGroupView` branch.

- [x] **5.4 — Routing (`viewer.js`)**
  - `controls_define`/`controls_clear` routing no longer has a `ControlGroupView`
    target; it falls back to the scene's `ThreeJsView` (existing global-panel
    behaviour for the additive `viz.add_slider` path).

- [x] **5.5 — Smoke**
  - `dev/src/js-tests/group-view-smoke.html`: `GroupView` of control views renders
    a titled panel; a `ThreeJsView`-less overlay check (mount a fake scene el with
    overlay children) confirms anchoring.

## Validation

`node --input-type=module --check` on all touched files + browser smoke pages +
`uv run pytest py/tests/viz/ -q` (frontend-shape tests stay green).

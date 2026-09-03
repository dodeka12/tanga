# Phase 4 — Retire the `controls_define` orphan-panel path

## Goal

Delete the legacy panel-control pipeline end to end: the backend `_push_controls*`
emission and the `push_controls` server callback, and the frontend
`handleControlsDefine`/`handleControlsClear` orphan-panel rendering plus its
toggle button. Controls now flow only through `view_layout`.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `py/tests/viz/test_controls.py`
- Edit: `dev/src/js-tests/control-registry.test.mjs`

## Steps

- [ ] **4.1 — Backend removal (`visualizer.py`, `server.py`)**
  - Remove `_push_controls`, `_push_controls_async`, `_push_controls_clear`, and
    `_grouped_control_ids` (`visualizer.py`).
  - Remove the `push_controls=self._push_controls_async` wiring in
    `Visualizer`'s server construction and the `await self._push_controls_async("")`
    call in the connect path.
  - In `server.py`, remove the `push_controls` ctor param/`_push_controls_cb`
    attribute and the per-scene `_push_controls_cb(...)` loop in the `ready` handler.

- [ ] **4.2 — Retire `ControlGroup` / `serialize_controls` (`_controls.py`)**
  - Remove `serialize_controls` and the `ControlGroup` dataclass (now unused).
  - Keep `_serialize_one_control` and `serialize_control_defs` (banners still use
    them via `_banner.py`).
  - Update `py/tests/viz/test_controls.py` to drop the `serialize_controls` /
    `ControlGroup` tests; keep `_serialize_one_control` tests.

- [ ] **4.3 — Frontend orphan-panel removal (`controls-panel.js`)**
  - Remove `handleControlsDefine`, `handleControlsClear`, `_createOrphanPanel`,
    `_ensureRoot`, `_ensureToggleButton`, `_positionPanel`, `_mountPanel`,
    `_setupDrag`, `_destroyAll`, and their panel-state (`_rootEl`, `_panelEls`,
    `_toggleBtn`, `_panelsHidden`).
  - Keep the `create*` factories, `_controlRegistry`, `applyControlValue`,
    `forgetControl`, `sendControlEvent`, `throttledSend`, `throttledFlush`.

- [ ] **4.4 — `three-view.js` routing removal**
  - Remove the `controls_define` / `controls_clear` branches and the
    `handleControlsDefine` / `handleControlsClear` import.

- [ ] **4.5 — JS test update (`control-registry.test.mjs`)**
  - Drop the `handleControlsDefine` import and the test that calls it; keep the
    layout-registry-survives test for `applyControlValue`/`forgetControl`.

## Validation

```
uv run pytest py/tests/viz/ -q
node --check py/pytanga/viz/templates/controls-panel.js py/pytanga/viz/templates/views/three-view.js
node --test 'dev/src/js-tests/control-registry.test.mjs'
```

## Notes

- This is the step that eliminates the `controls_define` → `_destroyAll()` wipe
  documented in `dev/todos/_done/viz-control-update-registry-reset.md`.
- Grep for `controls_define` / `handleControlsDefine` after editing to confirm no
  stray references remain outside generated `site/` output.

# Phase 10 — Group unification: `add_control_group` → `GroupView`

## Goal

Make `GroupView` the single control-group model. `add_control_group(...)` becomes
a facade that builds a `GroupView` (overlay anchor by default, optional 3D-object
anchor via `parent_id`), and the legacy fixed-panel `controls_define` group path
is retired — without breaking the existing call sites.

## Files

- Edit: `py/pytanga/viz/views.py` (`GroupView.parent_id`)
- Edit: `py/pytanga/viz/_controls.py` (deprecate `ControlGroup` serialization)
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/templates/views/group-view.js` + `build.js`
- Edit: `py/pytanga/viz/templates/controls-panel.js` (retire panel group render)
- Edit: `py/pytanga/viz/templates/controls-attached.js` (anchor via GroupView)
- Extend: `py/tests/viz/test_controls.py`, `test_views.py`, `test_layout_api.py`

## Steps

- [x] **10.1 — `GroupView.parent_id` (`views.py`)**
  - Add `parent_id: str | None = None`; serialize `"parent_id"` (only when set).

- [x] **10.2 — `add_control_group` facade (`visualizer.py`)**
  - Reimplement `add_control_group` / `_add_scene_group` to build a `GroupView`
    (title/icon/icon_only/collapsed/position/parent_id), resolve each referenced
    control id into its `*View` wrapper (via `scene._controls`), add them as
    children, and mount into the scene overlay (or global overlay for the base
    scene). Keep the same signature and return the group id.
  - Keep registering control handlers via the existing `(id, event)` registry.

- [x] **10.3 — `VizSceneHandle.add_control_group` (`_scene_handle.py`)**
  - Forward to the facade unchanged (signature-compatible).

- [x] **10.4 — Frontend anchor + retire panel path**
  - `build.js` / `group-view.js`: when `parent_id` is set, attach the group via
    `controls-attached.js` (`attachGroup`) instead of overlay anchoring.
  - Remove/stop calling `_createGroupPanel` + `serialize_controls` for groups;
    `handleControlsDefine` keeps only orphan controls (or is left as a no-op for
    groups). Keep `controls-attached.js` functional (now fed by `GroupView`).

- [x] **10.5 — Backward-compat check**
  - Existing examples/tests calling `add_control_group` still pass; the
    `parent_id` anchored case still renders (optional for the user, default is
    overlay).

- [x] **10.6 — Tests**
  - `add_control_group` produces a `GroupView` in the layout/overlay (not a
    `controls_define` group); `parent_id` serializes; a 3D-anchored group keeps
    working via the attach path (browser smoke).

## Validation

`uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_views.py py/tests/viz/test_layout_api.py -q && node --check py/pytanga/viz/templates/views/group-view.js && node --check py/pytanga/viz/templates/controls-attached.js`

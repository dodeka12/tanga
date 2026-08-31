# Phase 1 — Python `StackView`, `GroupView`, control views, `SceneView` overlay

## Goal

Extend the Python view model (`views.py`) with the new container + leaf types
and their `view_layout` serialization, keeping the module pure data + validation.

## Steps

- [x] **1.1 — `StackView(direction, children, *, **kwargs)`**
  - `direction` ∈ `{"vertical", "horizontal", "wrap"}` (validate, else `ValueError`).
  - Holds `children: list[View]` (no min-child count — unlike `SplitView`).
  - Serialize as a `stack` node: `direction` + `children` (reuse the shared size
    fields). No `movable`/`sizes` (flow layout has no splitters).
  - Exported via `views.__all__` and `pytanga.viz`.

- [x] **1.2 — `GroupView` (rename + redefine `ControlGroupView`)**
  - New class `GroupView(StackView)`:
    `GroupView(title, children, *, direction="vertical", position=None, collapsed=False, **kwargs)`.
  - Serialize as a `group` node: `title`, `direction`, `position`, `collapsed`,
    `children` + size fields.
  - **Remove** the old scene-bound `ControlGroupView` (and its `scene`/`group_id`
    fields). Update `__all__` (drop `ControlGroupView`, add `GroupView`).

- [x] **1.3 — Control views (`SliderView`/`ButtonView`/`DropdownView`)**
  - A common base `ControlView(View)` holding `id: str`, `label: str`, and the
    handler (`on_change`/`on_click`, `Handler | None`).
  - `SliderView(id, label="", min=0.0, max=1.0, step=0.01, default=None, on_change=None)`.
  - `ButtonView(id, label="", on_click=None)`.
  - `DropdownView(id, label="", options=(), default="", on_change=None)`.
  - Serialize as `slider_view` / `button_view` / `dropdown_view` nodes, reusing
    `_controls._serialize_one_control` for the kind-specific fields (build a
    throwaway `Slider`/`Button`/`Dropdown` or reuse the field logic directly).

- [x] **1.4 — `SceneView` overlay**
  - `SceneView(scene, *, overlay=None, **kwargs)` where `overlay: list[View]`.
  - Serialize `scene_view` with `children` = serialized overlay views (default
    `None`/empty → no `children` key).

- [x] **1.5 — `iter_scene_names`**
  - Only `SceneView` contributes a scene now (`GroupView` has no `scene`).
  - Keep dedup + DFS order; recurse into `StackView`/`GroupView` children and
    `SceneView.overlay` (overlay may reference scenes? — overlay views are
    controls/containers, not scenes, so only `SceneView.scene` is collected).

- [x] **1.6 — Tests (`test_views.py`)**
  - Rename `TestControlGroupView` → `TestGroupView`; assert `GroupView(...)`
    serializes as `group` with `title`/`direction`/`position`/`collapsed`.
  - Add `StackView` direction validation + `stack` serialization.
  - Add control-view serialization shape (`slider_view`/`button_view`/
    `dropdown_view` fields).
  - Add `SceneView` overlay serialization (`children`).
  - Update `test_scene_view_shape` if it asserts the (now possibly present)
    `children` key.

## Validation

`uv run pytest py/tests/viz/test_views.py -q` + `uv run ruff check
py/pytanga/viz/views.py py/tests/viz/test_views.py`

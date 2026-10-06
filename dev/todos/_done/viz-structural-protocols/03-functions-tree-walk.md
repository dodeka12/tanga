# Phase 3 — `functions.py` tree-walk

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace the `getattr(view, "scene"/"children"/"overlay", …)` duck-typing in the
`functions.py` tree-walk helpers with `isinstance` checks against the view-tree
`Protocol`s from `views/_base.py`.

## Files

- Edit: `py/pytanga/viz/views/functions.py`

## Steps

- [x] **3.1 — `iter_scene_names`**
  - Import `HasChildren`, `HasOverlay`, `HasScene` from `._base`.
  - Replace `scene = getattr(view, "scene", None)` + `isinstance(scene, str)`
    with `if isinstance(view, HasScene):` then read `view.scene` directly.
  - Replace the two `for child in getattr(view, "children"/"overlay", None) or ()`
    loops with `if isinstance(view, HasChildren):` / `if isinstance(view,
    HasOverlay):` guards followed by direct iteration.

- [x] **3.2 — the four `iter_*_views` helpers**
  - Apply the same `HasChildren`/`HasOverlay` replacement to `iter_scene_views`,
    `iter_control_views`, `iter_log_views`, and `iter_group_views` (each has two
    identical `getattr(…, "children"/"overlay", None) or ()` loops).
  - Keep the `isinstance(view, <ViewType>)` yield checks unchanged.

## Validation

```bash
uv run ty check && uv run ruff check . && uv run pytest py/tests/viz -q
```

## Notes

- `SceneView.scene` is already coerced to `str` (via `_coerce_scene_name`), so
  `HasScene.scene: str` is sound; the extra `isinstance(scene, str)` guard can
  be dropped.
- `SceneView` carries `scene` + `overlay` but no `children`; `StackView` /
  `SplitView` / `GroupView` / `MenuView` / `ToolbarView` carry `children`.  The
  `HasChildren` and `HasOverlay` `Protocol`s must stay separate (not merged).
- The `cast` at the `control_to_view` binding boundary is untouched.

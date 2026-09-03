# Viz Control Unification — Overview

**Created:** 2026-09-03 | **Status:** Planned | **Branch:** `feat/view-architecture`

## Goal

Retire the second, panel-based control pipeline (`Visualizer.add_*` →
`controls_define` → fixed orphan panel) and make every interactive control a
layout `*View`. `add_slider(...)` / `add_button(...)` / … become thin facades
that build the matching `SliderView` / `ButtonView` / …, register their handlers
through the single `(id, event)` path, and place them in an implicit per-scene
overlay `GroupView`. After this plan there is exactly **one** way to register,
render, and update a control: the layout/view system.

This closes the `SliderView` vs `add_slider` handler divergence (press/release),
removes the `controls_define` → `_destroyAll()` registry-wipe footgun
(`dev/todos/_done/viz-control-update-registry-reset.md`), and makes `add_*` and
`*View` offer the exact same feature set.

## Architecture (short)

- **Backend model** — `_controls.py` `Control` dataclasses stay the single source
  of truth; `views.py` `ControlView` subclasses wrap one each.
- **One handler registry** — `ControlHandlerRegistry` (`(id, event)`); one
  helper registers all handlers of a `ControlView` (change/click/press/release/
  cell_change/row_add/column_add/row_delete).
- **One display path** — `serialize_layout` → `view_layout` → `views/*.js`
  (`ControlView.render()` → shared `createX` factory in `controls-panel.js`).
- **`add_*` facade** — build `*View` + register + append to an implicit untitled
  `GroupView` (bottom-right), mounted exactly like `add_control_group` mounts
  explicit groups (global overlay for the base scene, scene overlay for named
  scenes).

## Fixed contract (up front)

### 1. `add_*` ↔ `*View` signature parity

Each `add_*` method and its `*View` counterpart expose the same features:

- `SliderView` and `add_slider` gain `on_press` / `on_release`.
- `add_slider` / `add_button` / `add_checkbox` gain `variant`
  (`EControlVariant`, default `DEFAULT`), matching the `*View`/`Control` classes.
- `control_to_view` forwards **every** control field, including
  `on_press` / `on_release`.

### 2. Implicit orphan panel

- `Visualizer` keeps `self._orphan_groups: dict[str, GroupView]`, lazily created
  per scene as `GroupView("", position=EAnchor.BOTTOM_RIGHT, collapsed=False)`
  and mounted the same way `_add_scene_group` mounts explicit groups.
- A bare `add_*` appends its `*View` to
  `_orphan_groups[scene_name].children`.

### 3. Control-id lookup

- `Visualizer` keeps
  `self._control_views: dict[str, tuple[str, ControlView]]`
  (control id → `(scene_name, ControlView)`), populated by every `_add_scene_*`
  and `_add_scene_group`, and removed by `_remove_scene_control` /
  `_clear_scene_controls`.
- `_resolve_control`, `set_control`, `get_control`, `update_control`, and
  `set_control_value` resolve through this registry first, falling back to the
  existing declarative-layout/dialog walk in `_resolve_control`.
- `_add_scene_group` resolves its `controls` ids via `_control_views` (reusing
  the stored `ControlView`, not `scene._controls` + `control_to_view`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-view-handler-parity.md](./01-view-handler-parity.md) | `*View`/`add_*` feature parity (`on_press`/`on_release`, `variant`) + complete `control_to_view` |
| 2 | [02-single-registration-path.md](./02-single-registration-path.md) | One `ControlView`→registry helper; register press/release |
| 3 | [03-add-controls-facade.md](./03-add-controls-facade.md) | `add_*` builds `*View` into an implicit overlay `GroupView`; unify lookup/removal/value-update |
| 4 | [04-retire-controls-define.md](./04-retire-controls-define.md) | Delete the `controls_define` orphan-panel path (backend + frontend) |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs, examples, changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (phase gates; full suite at the end)
- **JS:** `node --check py/pytanga/viz/templates/controls-panel.js py/pytanga/viz/templates/views/three-view.js`
- **Docs:** `uv run mkdocs build --strict`

## Non-goals

- No change to banners/dialogs — they already reuse the shared `createX` factories,
  `_controlRegistry`, and `_serialize_one_control` / `serialize_control_defs`.
- No per-control 3D anchoring on the orphan panel — 3D anchoring remains a
  `GroupView` / `add_control_group(..., parent_id=...)` concern only.
- No standalone/static-HTML control rendering (unchanged, as today).

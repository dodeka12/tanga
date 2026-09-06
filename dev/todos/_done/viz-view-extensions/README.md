# Viz View-Control Extensions — Overview

**Created:** 2026-09-01 | **Status:** Done | **Branch:** `feat/viz-view-extensions`

## Goal

Extend the Tanga layout/view system with four cohesive UI features, each built
on the **shared `View`/`ControlView` base** and the **single `(id, event)`
communication channel**:

1. **Group view chrome** — an optional icon left of the title (or icon-only), and
   a **borderless** fold/unfold button.
2. **Control variants** — a `StrEnum` of variants (`default`, `menu`) that render
   the same control (button/checkbox/slider) flat/borderless for menu rows.
3. **Menu system** — a hamburger dropdown (`click`-to-toggle) and a permanent
   horizontal strip, both nestable; global (base scene → global overlay) and
   per-pane (scene overlay).
4. **Dialog** — a title + arbitrary view-content container, closable by a user
   control or a ✕, as a **sibling** of `Banner`.

Finally, **unify** control-group creation onto `GroupView` (keeping the
`add_control_group` call backward-compatible, with optional 3D-object anchoring).

Also **unify the single-scene and layout view modes**: a "single view" is a layout
of one `SceneView`, so the overlay containers (menus, dialogs, control groups)
render identically in both, and overlay changes update connected browsers live.

## Architecture (short)

- **Backend model** lives in `py/pytanga/viz/`:
  - `_controls.py` — `Control` dataclasses, `ControlGroup`, `ControlHandlerRegistry`,
    `_serialize_one_control` / `serialize_controls`.
  - `views.py` — layout tree (`View`, `SceneView`, `StackView`, `GroupView`,
    `ControlView` + the `*View` control wrappers), `serialize_layout`.
  - `_banner.py` / (new) `_dialog.py` — dynamic overlay models.
  - `visualizer.py` / `_scene_handle.py` — public API + handler registration.
- **Frontend** lives in `py/pytanga/viz/templates/`:
  - `views/*.js` — `View`, `StackView`, `GroupView`, `ControlView`, `build.js`,
    `three-view.js` (per-pane `addOverlay`).
  - `controls-panel.js` — the `createButton`/`createCheckbox`/`createSlider`/…
    factories, `_controlRegistry`, `createIconElement`, injected CSS.
  - `overlay.js` + `views/overlay-view.js` — the **global** overlay singleton.
  - `banner.js` / `views/banner-view.js` — banner lifecycle (the dialog mirror).
  - `events.js` — `sendEvent(target, event, data)`.
- **Overlay containers (both exist already):**
  - Per-pane: `ThreeJsView.addOverlay` (absolute layer inside the pane, anchored
    by `view.position`), fed by `SceneView.overlay` → `scene_view.children`.
  - Global: `getOverlay()` singleton (`OverlayView`, `z-index: 500`), currently
    used only by banners / file browser.
- **One event channel:** frontend `sendEvent(id, "click"/"change"/"close", data)`
  → `server.py::_EVENT_MSG_MAP` → `Visualizer._dispatch_control_event` →
  handler from the `(id, event)` registry. New controls must not add a second
  channel.

## Wire/API contract (fixed up front)

### Control variants

```python
# py/pytanga/viz/_controls.py
class EControlVariant(StrEnum):
    DEFAULT = "default"
    MENU = "menu"
```

`Button`, `Checkbox`, `Slider` gain `variant: EControlVariant = EControlVariant.DEFAULT`.
`_serialize_one_control` emits `"variant": str(ctrl.variant)` for those three
kinds. Frontend `build.js` threads `node.variant`; `createButton` /
`createCheckbox` / `createSlider` add the `.tanga-menu-item` class when
`variant === "menu"`.

### GroupView chrome

`GroupView.__init__(..., icon: Icon | None = None, icon_only: bool = False)`.
Serialized as `"icon"` (str; omitted when `None`) and `"icon_only"` (bool). The
fold button is borderless and uses `material:expand_more` / `material:expand_less`.

### MenuView

`views.py` gains `MenuView(View)` with `_node_type = "menu"`:

- `trigger: Icon = EIconMaterial.MENU` (hamburger by default)
- `label: str = ""`
- `mode: Literal["dropdown", "bar"] = "dropdown"`
- `direction: StackDirection = "vertical"` (options-panel direction)
- `position: str | None = None` (anchor, when used as an overlay)
- `children: list[View]` (options; a child may be another `MenuView` = sub-menu)

Serialized node:

```json
{ "type": "menu", "id": "<gen>", "trigger": "material:menu", "label": "",
  "mode": "dropdown", "direction": "vertical", "position": null,
  "children": [ "…" ], "<size fields>": null }
```

### Global overlay slot

`serialize_layout(root, name="", overlay: list[View] | None = None)`:

```json
{ "type": "view_layout", "name": name, "scenes": [ "…" ],
  "overlay": [ "<serialized views>" ], "root": "…" }
```

`overlay` is omitted when empty. `viewer.js::_buildLayout` mounts each
`msg.overlay` view into `getOverlay()` (anchored by its `position`).

### `add_menu` convenience

```python
Visualizer.add_menu(
    mid=None, *, label="", trigger=EIconMaterial.MENU, mode="dropdown",
    direction="vertical", position=None, children=None, scene_name=None,
) -> str
```

`scene_name=None` → **global** menu (base scene → global overlay). Per-pane menus
are declared with `SceneView(overlay=[MenuView(position=...)])`.

### Dialog

```python
# py/pytanga/viz/_dialog.py
Dialog(id, title="", content: View, align_x=0.5, align_y=0.5,
       dismissable=True, on_close=None)
```

Messages:

```json
{ "type": "dialog_define", "scene": null, "id": "dlg_1", "title": "",
  "align_x": 0.5, "align_y": 0.5, "dismissable": true,
  "content": "<serialized view node>" }
{ "type": "dialog_remove", "scene": null, "id": "dlg_1" }
{ "type": "dialog_clear", "scene": null }
```

Close: frontend `sendEvent(dialogId, "close")` → existing `_dispatch_control_event`
`close` branch (handler registered under `(dialog_id, "close")`).

### Group unification

`add_control_group(...)` becomes a facade that builds a `GroupView` (resolving
referenced control ids to `*View` wrappers) and mounts it into the scene overlay;
`GroupView` gains `parent_id: str | None = None` for optional 3D-object anchoring.
The legacy fixed-panel `controls_define` path is retired for groups.

### View-mode unification

A single scene is served as a one-pane layout: `StackView("vertical",
[SceneView(scene_name)])` merged with the global overlay (base scene `""` only)
and per-scene overlays. `Visualizer._scene_layout_for(scene_name)` returns its
serialized `view_layout`; the server resolves a layout payload for every `ready`
(`layout` → `_layout_callback`, else `_scene_layout_callback(scene_name)`), and the
frontend always renders through `_buildLayout`. Overlay changes re-serialize and
re-push the affected layout (per session, not broadcast) so connected browsers
stay in sync.

## Decisions (confirmed)

- Menu placement: **scene overlay with anchor position**; `add_menu(scene=None)`
  → global overlay; per-pane via `SceneView(overlay=[MenuView(...)])`.
- Menu open interaction: **click-to-toggle** (sub-menus also click-to-toggle).
- Dialog is a **sibling** of `Banner` (parallel `_dialog.py` / `dialog.js`), not a
  banner mode.
- Variants are a **`StrEnum`** (`EControlVariant`), extensible later.
- Control groups: only `GroupView`; `add_control_group` keeps backward
  compatibility. Anchoring a group to a 3D object stays supported but is
  optional (default is overlay anchor).
- View modes: a single scene view is a one-`SceneView` layout; the server always
  serves a `view_layout` and the frontend always renders through the layout tree.
  Overlay changes re-push `view_layout` at runtime (targeted per session), rather
  than reordering `VisualizerApp`'s `init()`-after-connect lifecycle.
- Global overlay (base-scene menus) is served on every view, including named-scene
  single views (consistent with layout mode).
- Standalone HTML export is unaffected (separate `export/` path); it stays
  single-scene, no controls/layouts.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-control-variant-enum.md](./01-control-variant-enum.md) | `EControlVariant` + `variant` on button/checkbox/slider (model, serialization, views, tests) |
| 2 | [02-group-view-icon-toggle.md](./02-group-view-icon-toggle.md) | `GroupView` icon/icon_only + borderless fold (Python + JS + tests) |
| 3 | [03-example-group-view.md](./03-example-group-view.md) | Example: group icons + borderless fold |
| 4 | [04-menu-model-overlay-api.md](./04-menu-model-overlay-api.md) | `MenuView` model + `serialize_layout` overlay slot + `add_menu` API (+ tests) |
| 5 | [05-menu-frontend.md](./05-menu-frontend.md) | `menu-view.js` (dropdown/bar/nesting) + `build.js` + `viewer.js` global-overlay mount (+ smoke) |
| 6 | [06-example-menu.md](./06-example-menu.md) | Example: menus (dropdown, sub-menus, bar, global + per-pane) |
| 7 | [07-dialog-model-api.md](./07-dialog-model-api.md) | `_dialog.py` + `show_dialog`/`remove_dialog`/`clear_dialogs` + close callback (+ tests) |
| 8 | [08-dialog-frontend.md](./08-dialog-frontend.md) | `dialog-view.js` + `dialog.js` + `viewer.js` routing (+ smoke) |
| 9 | [09-example-dialog.md](./09-example-dialog.md) | Example: dialog with view content + close control |
| 10 | [10-group-unification.md](./10-group-unification.md) | `add_control_group` → `GroupView` facade (+ optional `parent_id` anchor), retire fixed-panel path (+ tests) |
| 11 | [11-example-group-unification.md](./11-example-group-unification.md) | Example: unified `add_control_group` (overlay + optional 3D anchor) |
| 12 | [12-scene-layout-resolver.md](./12-scene-layout-resolver.md) | Per-scene single-`SceneView` layout resolver (`_scene_layout_for`) (+ tests) |
| 13 | [13-server-always-layout.md](./13-server-always-layout.md) | Server always serves `view_layout`; track `session.layout` (+ tests) |
| 14 | [14-frontend-single-path.md](./14-frontend-single-path.md) | Frontend always builds the layout tree; teardown + unified routing |
| 15 | [15-live-overlay-repush.md](./15-live-overlay-repush.md) | Live `view_layout` re-push on overlay changes |
| 16 | [16-integration-examples.md](./16-integration-examples.md) | Verify/migrate examples + regression tests |
| 17 | [17-docs-changelog.md](./17-docs-changelog.md) | Docs (view modes + API) + changelog + export gate + full validation |
| 18 | [18-group-unification-consolidation.md](./18-group-unification-consolidation.md) | Re-verify `add_control_group` in single-scene + layout; extend the group example |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (targeted per phase; full suite in
  the final phase).
- **JS syntax:** `node --check <module>` on new/edited `templates/**/*.js`.
- **JS DOM smoke:** browser pages under `dev/src/js-tests/` (mirroring
  `group-view-smoke.html`) for the borderless toggle, menu nesting, dialog close.
- **Examples/docs:** `uv run python tools/generate-example-docs.py --check` after
  any example edit; `uv run mkdocs build --strict` in the final phase.
- **Export regression:** `uv run pytest py/tests/viz/test_export_static.py
  py/tests/viz/test_export_camera.py py/tests/viz/test_export_renderers.py -q` in
  the final phase (the unification must not touch the standalone export path).

## Non-goals

- Migrating the existing internal warning banners (SDF/WebGL, version mismatch).
- Drag-to-reposition menus/dialogs (fixed `position`/`align` only).
- Persisting menu/dialog state across reconnects.
- Menus per *scene name* (only global + per-`SceneView`-pane).
- Exporting controls/split views to standalone HTML (export stays single-scene).
- Changing the URL scheme (`/`, `/{name}`, `?view=`).
- Reordering `VisualizerApp`'s `init()`-after-connect lifecycle.

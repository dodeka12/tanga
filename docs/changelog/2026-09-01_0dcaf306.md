# Changes since version 1.14.1

## New Features

- **Control variants** — a new `EControlVariant` enum (`default` / `menu`) and a
  `variant=` parameter on `ButtonView` / `CheckboxView` / `SliderView` (backed by
  the shared `Button` / `Checkbox` / `Slider` controls), so a control can render
  flat and borderless for menu rows.
- **Group view chrome** — `GroupView` accepts an optional leading `icon` and an
  `icon_only` mode (icon without a title), and its fold/unfold button is now a
  borderless icon.
- **Anchor position enum** — a new `EAnchor` enum (corner anchors `top-left` /
  `top-right` / `bottom-left` / `bottom-right` plus centered edge anchors
  `top` / `bottom` / `left` / `right`) captures the allowed overlay/panel
  positions used by `GroupView` and `MenuView`.
- **Menu system** — a new `MenuView` (a hamburger `dropdown` or a permanent
  `bar` of options, with nestable sub-menus), `Visualizer.add_menu()` for global
  menus, and a top-level `serialize_layout(overlay=...)` slot that mounts views
  in the full-screen overlay. Menu controls are automatically styled with the
  `MENU` variant (`override_variant=True` by default).
- **Dialog** — a new `Dialog` overlay (`Visualizer.show_dialog` /
  `remove_dialog` / `clear_dialogs`, plus `VizSceneHandle` and `_async`
  variants) renders a titled dialog whose body holds arbitrary view content and
  whose title bar drags it with the mouse (clamped to the viewport);
  `dismissable=False` makes it modal (a dimmed backdrop blocks the scene and
  there is no ✕).
- **Unified control groups** — `add_control_group` now builds a `GroupView`
  anchored as an overlay (optionally attached to a 3D object via `parent_id`),
  replacing the fixed-panel group rendering.
- **View-mode unification** — a single scene is served as a one-`SceneView`
  layout, so the frontend always renders through the layout tree; overlays
  (control groups, menus, dialogs) behave identically in single-scene and
  split-view modes, and overlay changes update connected browsers live.
- **Examples** — new `group_view_icons.py` (scene-overlay groups with icons),
  `menus/menu_demo.py` (global + per-pane menus, sub-menus, and a menu bar), and
  `dialogs/dialog_demo.py` (a dialog with view content, a menu-bar reopen, and a
  modal variant).

## Breaking Changes

- **Control-group model is `GroupView`** — control groups are now rendered as
  `GroupView` overlays (overlay-anchored, or `parent_id`-attached to a 3D
  object); the legacy fixed-panel group rendering path is retired.  The
  `add_control_group` call signature is unchanged (backward compatible).

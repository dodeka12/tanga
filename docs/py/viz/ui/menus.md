# Menus

`MenuView` is a menu container — a hamburger `dropdown` or a permanent horizontal
`bar` of options, with nestable sub-menus.  `children` are the options (control
views); a child may be another `MenuView`, which forms a nested sub-menu.
`_node_type` is `"menu"`.

```python
MenuView(
    label="",           # str
    children=None,      # list[View] | None — options (control views / sub-menus)
    *,
    trigger_icon=None,  # Icon | None — optional leading icon (e.g. EIconMaterial.MENU)
    mode="dropdown",    # "dropdown" | "bar"
    direction=None,      # StackDirection | None — "horizontal" for bars, else "vertical"
    position=None,      # EAnchor | None — corner or centered-edge anchor (e.g. "top-right", "bottom")
    override_variant=True,  # bool — auto-set the MENU variant on control children
    **kwargs,           # forwarded to View (sizes)
)
```

- `mode="dropdown"` renders a click-to-toggle trigger with the options in a
  hidden panel (outside-click or `Escape` closes it); a nested `MenuView` opens
  beside its parent as a sub-menu.
- `mode="bar"` renders the options always-visible in a horizontal strip; a
  nested `MenuView` renders as a plain menu-bar label and opens its panel
  downwards (flipping upwards near the bottom of the viewport).
- `override_variant=True` (default) forces every eligible control in the subtree
  to the `MENU` variant, so options render flat without setting `variant=` by
  hand.

## Global vs per-pane

Global menus are declared as a `MenuView` in the default layout's overlay (via
`viz.add(menu)` or `viz.set_layout`); per-pane menus are declared with
`SceneView(overlay=[MenuView(...)])`:

```python
menu = MenuView(
    label="Settings",
    trigger_icon=EIconMaterial.MENU,
    children=[
        ButtonView("fit", label="Fit camera", on_click=on_fit),
        SliderView("radius", label="Radius", on_change=on_radius),
    ],
)
viz.add(menu)  # mounts in the default layout's overlay
```

## Examples

- `py/examples/viz/ui/menus/menu_demo.py` — per-pane and bar menus with nested
  sub-menus.
- `py/examples/viz/ui/menus/file_open_menu.py` — a menu bar with a File → Open…
  file dialog.

## See Also

- [Control Views](control-views.md) — the `xxxView` classes that fill a menu
- [Dialogs](dialogs.md) — `show_dialog` for view-based pop-ups

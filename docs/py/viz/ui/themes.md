# Themes

The viewer's UI chrome (controls, panels, banners, dialogs, menus) is themed via
CSS under `py/pytanga/viz/templates/themes/`.  A **theme** is an ordered list of
CSS files resolved from `registry.json`: `base.css` (design tokens + global
rules) → default tokens → theme tokens → per-control/view sheets → theme
overrides.

## Selecting a theme

The active theme is viewer-global and defaults to `"dark"`:

```python
from pytanga.viz import Visualizer

viz = Visualizer()
viz.set_theme("light")   # validates + pushes a `theme_define` to all clients
print(viz.theme)         # "light"
```

`set_theme` switches connected browsers live (no page reload) by swapping the
`<link data-tanga-theme>` tags; it raises `KeyError` for an unknown theme id.

## Available themes

```python
from pytanga.viz import list_themes, theme_css_files, theme_label

list_themes()                 # ["dark", "light", "pastel"]
theme_label("light")          # "Light"
theme_css_files("light")      # the ordered CSS file list
```

## Themed exports

`export_snapshot` / `export_figure` (and the scene handles) accept `theme=` to
pack a specific theme's CSS into the self-contained HTML (default: the active
theme):

```python
viz.export_snapshot("scene.html", theme="pastel")
```

## Custom themes

Create and load your own theme with `copy_theme` / `register_theme` and iterate
live with `enable_theme_auto_reload`. See [Custom themes](custom-themes.md) for the
full walkthrough and the themeable-token reference.

See the examples:

- [Control theming](../../examples/viz/ui/controls/control_theming.md) — controls styled from the theme CSS.
- [Theme switching](../../examples/viz/ui/themes/theme_switching.md) — runtime `set_theme` switching.
- [Custom theme override](../../examples/viz/ui/themes/custom_theme_override.md) — a `pastel` theme with full button/checkbox overrides.

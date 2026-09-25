# UI & Controls

This section documents the viewer's user-interface surface: the declarative
control views (`SliderView`, `ButtonView`, `TableView`, …), the layout model
(`SplitView`/`StackView`/`SceneView`), overlays and menus, dialogs and banners,
theming, and the read-only display views.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Controls](controls.md) | The control kinds (`SliderView`, `DropdownView`, `ButtonView`, `TableView`, …) and their handler payloads |
| [Control Views (xxxView)](control-views.md) | The declarative `xxxView` layout/control classes and their constructor signatures |
| [Layouts — Split Views & Controls](layouts.md) | `SplitView`/`SceneView`/`GroupView` panes and control views inside a `VisualizerApp` |
| [Split Views](split-views.md) | The view hierarchy, `Size` units, splitters, overlays, per-pane cameras |
| [Runtime Updates](runtime-updates.md) | Update a layout, background image, or image view at runtime without rebuilding the UI |
| [Menus](menus.md) | `MenuView` — dropdown vs bar, nested sub-menus, global vs per-pane |
| [Dialogs](dialogs.md) | `show_dialog`, the `Dialog` parameters, `FileChooserDialog` |
| [Display Views](display-views.md) | `LabelView` / `MarkdownView` / `LogView` read-only content views |
| [Banners](banners.md) | `alert` / `confirm` / `show_banner`, alignment, modal banners |
| [File Chooser](file-chooser.md) | `FileChooserView`, the backend-driven browser, `FileChooserDialog` |
| [Themes](themes.md) | `set_theme()` runtime switching, `list_themes()`, themed exports |
| [Custom Themes](custom-themes.md) | `copy_theme`/`register_theme`, tokens + overrides, auto-reload |

## Related

- [Visualizer App](../app/index.md) — `VisualizerApp` lifecycle and handlers
- [Object Interaction](../interaction/object-interaction.md) — click/drag/scroll on scene entities

# Visualizer App

`VisualizerApp` is the highest-level way to build interactive visualizations: a
managed lifecycle (start → `init` → wait → `cleanup` → stop) plus interactive
controls (sliders, dropdowns, buttons, groups) and async handlers.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Quickstart](app.md) | Subclassing `VisualizerApp`, the lifecycle, your first controls |
| [Controls](controls.md) | `add_slider`/`add_dropdown`/`add_button`/`add_group`, scene-scoped controls |
| [Layouts — Split Views & Controls](layouts.md) | `SplitView`/`SceneView`/`GroupView` panes and control views inside a `VisualizerApp` |
| [Handlers & Lifecycle](handlers.md) | The handler contract, `ControlEvent`, async patterns, the full lifecycle |
| [Banners & Dialogs](banners.md) | `alert`/`confirm`/`show_banner`, alignment, modal banners, offloading work from handlers |
| [File Chooser](file-chooser.md) | `add_file_chooser`, the backend-driven file browser, `open_file_chooser` |

# Visualizer App

`VisualizerApp` is the highest-level way to build interactive visualizations: a
managed lifecycle (start → `init` → wait → `cleanup` → stop) plus interactive
controls (sliders, dropdowns, buttons, groups) and async handlers.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Quickstart](app.md) | Subclassing `VisualizerApp`, the lifecycle, your first controls |
| [Handlers & Lifecycle](handlers.md) | The handler contract, `ControlEvent`, async patterns, the full lifecycle |

The UI surface it drives — controls, layouts, menus, dialogs, banners, and
themes — is documented in the [UI & Controls](../ui/index.md) section.

# Visualizer

The `Visualizer` class is the core of `pytanga.viz`: it owns the WebSocket
server, the scene graph, the camera, animation, and the low-level
pointer-interaction API. (`VisualizerApp` builds on top of it — see the
[Visualizer App](../app/index.md) section.)

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Visualizer](visualizer.md) | Creating a visualizer, `add()`/`new()`/`viz(...)`, scenes, styles, labels |
| [Multi-Scene](multi-scene.md) | Named scenes, `viz.scene()`/`VizSceneHandle`, navigation, browser targeting |
| [Scene Graph & Transforms](scene-graph.md) | `VizGroup`/`VizObjectRef` hierarchy, transforms, compound animation |
| [Camera & Controls](camera.md) | `CameraConfig2d`/`CameraConfig3d`, `View2DConfig`/`View3dConfig` |
| [Animation](animation.md) | Frame-by-frame `animate()` and keyframe `animate_to()`/`Timeline` |
| [Themes](theming.md) | `set_theme()` runtime switching, `list_themes()`, themed exports |
| [Object Interaction](../interaction/object-interaction.md) | Click/drag/scroll handlers on scene entities |

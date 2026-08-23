# Controls

Controls are created on the `Visualizer` instance (`self.viz`) and appear as an
overlaid control panel in the browser. Each control takes a unique id and an
**async** handler callback.

For the handler contract and the `VisualizerApp` lifecycle, see
[Handlers & Lifecycle](handlers.md).

## `add_slider`

```python
self.viz.add_slider(
    "sphere_b_x",
    label="X Position",
    min=-3.5,
    max=3.5,
    step=0.02,
    default=2.5,
    on_change=self.on_slider,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID (unique string) |
| `label` | `str` | `""` | Label text displayed above the slider |
| `min` | `float` | `0.0` | Minimum value |
| `max` | `float` | `1.0` | Maximum value |
| `step` | `float` | `0.01` | Step increment |
| `default` | `float` | `min` | Initial value |
| `on_change` | `Callable` | `None` | Async callback: `(value: float, event: ControlEvent) -> None` |

## `add_dropdown`

```python
self.viz.add_dropdown(
    "mode",
    label="Display",
    options=["Both", "Sphere A only", "Sphere B only"],
    default="Both",
    on_change=self.on_mode,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `options` | `list[str]` | `[]` | Dropdown choices |
| `default` | `str` | `""` | Initial selection |
| `on_change` | `Callable` | `None` | Async callback: `(value: str, event: ControlEvent) -> None` |

## `add_button`

```python
self.viz.add_button(
    "reset",
    label="Reset",
    on_click=self.on_reset,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Button text |
| `on_click` | `Callable` | `None` | Async callback: `(value: None, event: ControlEvent) -> None` |

## `add_group`

Groups controls into a collapsible panel at a fixed position:

```python
self.viz.add_group(
    "viewport_controls",
    title="Controls",
    controls=["sphere_b_x", "mode", "reset"],
    position="bottom-right",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gid` | `str` | *(required)* | Group ID |
| `title` | `str` | `""` | Group header (empty = no header) |
| `controls` | `list[str]` | `[]` | Ordered list of control IDs |
| `position` | `str` | `"bottom-right"` | `"top-left"`, `"top-right"`, `"bottom-left"`, `"bottom-right"` |
| `collapsed` | `bool` | `False` | Start collapsed |
| `on_toggle` | `Callable` | `None` | Async callback: `(value: bool, event: ControlEvent) -> None` |

Controls must be created **before** the group that references them.

## Removing controls

```python
self.viz.remove_control("sphere_b_x")
self.viz.remove_group("viewport_controls")
self.viz.clear_controls()  # remove all
```

## Scene-scoped controls

Controls are scoped per-scene — when using :class:`VizSceneHandle`, controls
are created on the target scene and only appear for browsers viewing that
scene:

```python
detail = viz.scene("detail")
detail.add_slider("radius", label="Radius", min=0.1, max=5.0, on_change=on_radius)
detail.add_button("reset", label="Reset", on_click=on_reset)
detail.add_group("detail_controls", controls=["radius", "reset"], title="Detail")
```

Controls and groups are pushed only to browsers viewing the ``"detail"`` scene.
This allows different scenes to have completely independent control panels.

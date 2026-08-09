# Phase 5 — Viz Backend

Add a `space_dim` parameter to the visualizer pipeline (Python side) so the
frontend knows when to render in 2D mode (orthographic camera, pan/zoom controls).

No entity/operator changes — entities remain 3D dataclasses; the renderers
already handle `[x, y, z]` arrays. Full 3D entities (e.g. `Sphere` with
non‑zero `z`, `Plane` tilted in space) also work in 2D mode — they render
faithfully from the orthographic top‑down perspective with no extra code.
<diff>
<diff>
<diff>
<diff>
<diff>
<diff>

## Files to Modify

### `py/pytanga/viz/scene.py` — `SceneConfig`

Add one field and include it in serialization:

```python
@dataclass
class SceneConfig:
    space_extent: float = 10.0
    show_grid: bool = True
    show_axes: bool = True
    background_color: str = "#1a1a2e"
    camera: CameraConfig | None = None
    title: str = "Tanga 3D Viewer"
    annotation: str | None = None
    name: str = ""
    space_dim: int = 3  # NEW: 2 or 3
```

In `to_dict()`, add:
```python
result["space_dim"] = self.space_dim
```

### `py/pytanga/viz/visualizer.py` — `Visualizer.__init__()`

Add `space_dim: int = 3` parameter:
```python
def __init__(
    self,
    *,
    port: int = 8765,
    host: str = "localhost",
    open_browser: bool | None = None,
    reuse_existing: bool = True,
    opns: bool = True,
    title: str = "Tanga 3D Viewer",  # auto-adjusted below
    annotation: str | None = None,
    space_extent: float = 10.0,
    show_grid: bool = True,
    show_axes: bool = True,
    background_color: str = "#1a1a2e",
    camera: CameraConfig | None = None,
    space_dim: int = 3,  # NEW
) -> None:
```

Auto-adjust defaults when `space_dim == 2`:
```python
if space_dim == 2 and title == "Tanga 3D Viewer":
    title = "Tanga 2D Viewer"
```

Pass `space_dim` to `SceneConfig`:
```python
self._config = SceneConfig(
    space_extent=space_extent,
    show_grid=show_grid,
    show_axes=show_axes,
    background_color=background_color,
    camera=camera,
    title=title,
    annotation=annotation,
    name="",
    space_dim=space_dim,  # NEW
)
```

Also pass `space_dim` when creating new scenes in `self.scene()`:
```python
def scene(self, name: str) -> VizSceneHandle:
    if name not in self._scenes:
        cfg = SceneConfig(
            ...
            space_dim=self._config.space_dim,  # inherit from visualizer
        )
```

### `py/pytanga/viz/_app.py` — `VisualizerApp.__init__()`

Add `space_dim: int = 3` parameter, forward to `Visualizer`:
```python
def __init__(
    self,
    *,
    ...
    space_dim: int = 3,  # NEW
    ...
) -> None:
    self.viz = Visualizer(
        ...
        space_dim=space_dim,  # NEW
        ...
    )
```

### `py/pytanga/viz/_figure.py` — `FigureConfig`

Add `space_dim: int = 3` field:
```python
@dataclass
class FigureConfig:
    ...
    space_dim: int = 3  # NEW
```

Add to `to_dict()`:
```python
result["space_dim"] = self.space_dim
```

### `py/pytanga/viz/_scene_handle.py` — `VizSceneHandle`

No changes needed. The scene handle inherits config from the parent Visualizer
via `SceneConfig`.

### `py/pytanga/viz/serializer.py`

No changes needed. Entity serialization is dimension‑agnostic — `[x, y, z]`
arrays work for both 3D and 2D. In 2D mode, `x` and `y` determine the entity's
on‑screen position while `z` controls overlay draw order: larger positive `z`
values render on top of smaller ones (enforced by the frontend via
`renderOrder` and `depthTest` adjustments in the camera + renderer setup).

### `py/pytanga/viz/_style_dict.py`

No changes needed. Style keys (`"Point"`, `"Line"`, etc.) are the same for 2D.

### `py/pytanga/viz/server.py` and `py/pytanga/viz/_controls.py`

No changes needed. The server just passes JSON config to the frontend; the
frontend interprets `space_dim`.

## Implementation Checklist

- [ ] 5.1  Add `space_dim: int = 3` field to `SceneConfig` in `viz/scene.py`
- [ ] 5.2  Add `"space_dim"` to `SceneConfig.to_dict()` output
- [ ] 5.3  Add `space_dim: int = 3` parameter to `Visualizer.__init__()` in `viz/visualizer.py`
- [ ] 5.4  Auto‑adjust title from `"Tanga 3D Viewer"` → `"Tanga 2D Viewer"` when `space_dim == 2`
- [ ] 5.5  Pass `space_dim` to `SceneConfig` in `Visualizer.__init__()`
- [ ] 5.6  Inherit `_config.space_dim` when creating new scenes in `Visualizer.scene()`
- [ ] 5.7  Add `space_dim: int = 3` to `VisualizerApp.__init__()`, forward to `Visualizer`
- [ ] 5.8  Add `space_dim: int = 3` to `FigureConfig`, include in `to_dict()`
- [ ] 5.9  Verify: `viz = Visualizer(space_dim=2)` produces `SceneConfig` with `space_dim == 2`
- [ ] 5.10 Verify: JSON from `SceneConfig.to_dict()` includes `"space_dim": 2`
- [ ] 5.11 Verify: `Visualizer(space_dim=2).title` defaults to `"Tanga 2D Viewer"`
- [ ] 5.12 Verify: `Visualizer(title="Custom", space_dim=2)` does NOT override custom title
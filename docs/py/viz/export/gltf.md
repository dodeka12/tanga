# glTF Export

Export the scene as a glTF 2.0 binary (`.glb`) — a single-file format you can
open in Blender, macOS Preview, Windows 3D Viewer, `<model-viewer>`, or any
glTF-compatible tool.

```python
viz = Visualizer()
viz(Point(1, 2, 3), color="#ff4444")
viz(Sphere(Point(0, 0, 0), radius=2), opacity=0.3)

viz.export_glb("scene.glb")
```

Notes:

- Only **entities** are exported — overlay layers (labels, texture labels,
  title, annotation) are excluded because glTF has no universal representation
  for them.
- Path resolution matches the other exports: relative paths resolve against the
  current working directory, `~` expands, parent directories are created, and a
  missing extension is appended (`"scene"` → `"scene.glb"`).
- Pass `overwrite=True` to replace an existing file.
- Like all file exports, no server is required — the scene is read directly
  from memory.

## Use cases

| Tool | Notes |
|------|-------|
| Blender | Import for high-quality offline rendering or further editing |
| `<model-viewer>` | Embed a 3D model in a web page |
| macOS Preview / Windows 3D Viewer | Quick local inspection |
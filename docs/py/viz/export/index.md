# Export

This section covers everything you can take *out* of the visualizer: standalone
HTML documents, glTF/GLB models, still images, and MP4 video.

Export reads directly from the in-memory scene, so **no server is required**
for the file-producing exports (HTML, glTF, figure snippets):

```python
viz.export_snapshot("scene.html")   # self-contained HTML
viz.export_glb("scene.glb")         # glTF binary
viz.export_figure("figure.html")    # embeddable presentation snippet
```

Screenshots and video capture are different — they capture the **live browser
viewport** and therefore need the server running (and, for video, `ffmpeg` on
your `PATH`). Those live in the [Video & Image Export](video-image.md) page.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Standalone HTML](html.md) | Self-contained HTML (static and animated), figure snippets for presentations, `FigureStyle`/`AnimStyle` |
| [glTF Export](gltf.md) | Binary `.glb` export for Blender, `<model-viewer>`, and other 3D tools |
| [Video & Image Export](video-image.md) | PNG screenshots and MP4 video capture from the live browser (requires `ffmpeg`) |

## Example scripts

| Script | Topic |
|--------|-------|
| [`demo_export_html.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_html.py) | Self-contained HTML and glTF export |
| [`demo_export_figure.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_figure.py) | Presentation figure export with `FigureStyle` |
| [`demo_animated_export.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animated_export.py) | Animated HTML export with JS playback engine |
| [`demo_screenshot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_screenshot.py) | Programmatic PNG screenshot |
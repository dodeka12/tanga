# Export & Capture

Export is now handled directly on `Visualizer` (and `VizSceneHandle`) —
`SceneExporter` is deprecated:

```python
viz.export_snapshot("scene.html")
viz.export_glb("scene.glb")
viz.export_figure("figure.html")
```

For export-only workflows where no browser is needed, no server is required —
exports read directly from the in-memory scene:

```python
viz = Visualizer()
# add entities, then export...
viz.export_snapshot("scene.html")
```

If you also want a live viewer while exporting, call `viz.show()` first.

Screenshot and video capture still live on `SceneExporter` (deprecated) for
now — see the [Screenshots](#screenshots) and [Video Capture](#video-capture)
sections.

See the example scripts [`demo_export_html.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_html.py),
[`demo_export_figure.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_figure.py),
[`demo_screenshot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_screenshot.py), and
[`demo_animated_export.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animated_export.py).

## HTML Export

Self-contained HTML file — double-click to view, no Python server needed:

```python
viz.export_snapshot("scene.html")
```

Embeds entity data and renderer modules inline. Three.js loads from CDN.

## glTF 2.0 Export

Binary `.glb` file for Blender, `<model-viewer>`, or any glTF viewer:

```python
viz.export_glb("scene.glb")
```

## Figure Export (Presentations)

HTML snippet (`<div>` + `<script>`) for embedding in reveal.js, Slidev, or
any HTML-based presentation:

```python
from pytanga.viz import FigureStyle

viz.export_figure(
    "figure.html",
    style=FigureStyle(
        width=800,
        height=600,
        background="transparent",
        auto_rotate=True,
        border_radius="8px",
    ),
)
```

**`FigureConfig`** (on `SceneExporter.figure_config`):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | `str` | `"Tanga 3D Viewer"` | Viewport title |
| `target` | `str` | `"body"` | CSS selector for DOM mount point |
| `annotation` | `str \| None` | `None` | Markdown annotation text |
| `footer` | `str \| None` | `None` | Markdown footer below canvas |
| `background` | `str` | `"#1a1a2e"` | CSS background |
| `browser_width` | `int \| None` | `None` | Standalone window width |
| `browser_height` | `int \| None` | `None` | Standalone window height |

**`FigureStyle`:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | `int` | `800` | Canvas width in px |
| `height` | `int` | `600` | Canvas height in px |
| `background` | `str` | `"transparent"` | CSS background |
| `auto_rotate` | `bool` | `False` | Auto-rotate the camera |
| `show_title` | `bool` | `True` | Show title overlay |
| `show_annotation` | `bool` | `True` | Show annotation panel |
| `border_radius` | `str` | `"0"` | CSS border-radius |
| `responsive` | `bool` | `False` | Fill parent container, resize with window |

**Standalone window:** `viz.open_snapshot()`

**String output:** `snippet = viz.export_figure()`

### Keyboard Shortcuts in Exported Figures

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` / `Cmd+S` | Download a PNG snapshot |
| `r` | Toggle camera auto-rotation |

These shortcuts work in all exported HTML files (static, figure, and animated).
Set `auto_rotate=True` in `FigureStyle` to enable auto-rotation on load; the
user can press `r` to toggle it.

## Screenshots

**Browser shortcut:** `Ctrl+S` (or `Cmd+S` on macOS) downloads a PNG of the
current viewport.

**Programmatic screenshot:**

```python
exporter.screenshot("figure.png")
exporter.screenshot("figure_hd.png", width=1920, height=1080)
```

Sends a screenshot request over WebSocket — the browser captures its canvas
and returns the PNG data. Blocks until received or timeout.

## Video Capture

Capture animation frames as sequenced PNGs, then stitch into MP4 with ffmpeg:

```python
exporter.start_capture(width=800, height=600)

for frame in range(90):  # 3 seconds at 30 FPS
    viz.update_entity(point_id, Point(...))
    viz.flush()
    exporter.capture_frame()
    viz.sleep_ms(33)

exporter.finish_capture(video_path="orbit.mp4", fps=30)
```

- `start_capture(*, folder, width, height)` — begin capture session
- `capture_frame(*, timeout)` — capture sequenced PNG (`frame_0000.png`, …)
- `finish_capture(*, video_path, fps, crf, keep_images)` — optional MP4, optional temp cleanup

ffmpeg must be installed on the system PATH. Temp folders auto-clean after
video creation unless `keep_images=True`. User-specified folders are never
deleted.

**State machine:** `IDLE → CAPTURING → IDLE`. Invalid transitions raise
`RuntimeError`.

## Animated HTML Export

Record entity state during a Python animation loop and embed as a
self-contained HTML file with JS playback controls:

```python
from pytanga.viz import AnimStyle, FigureStyle

recording = viz.start_animation_recording()

for frame in range(90):
    viz.update_entity(point_id, Point(...))
    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

# Figure snippet (for presentations)
viz.export_figure(
    "animated_figure.html",
    animation=recording,
    style=FigureStyle(width=800, height=600, responsive=True),
    anim_style=AnimStyle(fps=30, loop=True),
)

# Full-page standalone document
viz.export_snapshot(
    "animated_scene.html",
    animation=recording,
    anim_style=AnimStyle(fps=30, loop=True),
)
```

**`AnimStyle`** controls playback behaviour:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fps` | `int` | `30` | Playback frame rate |
| `loop` | `bool` | `True` | Loop the animation |
| `show_controls` | `bool` | `True` | Show play/pause/scrub controls |
| `compress` | `bool` | `False` | Gzip-compress embedded animation data (70–80% smaller file, ~5 ms decompression at page load) |

The exporter's `_default_anim_style` has defaults `fps=30`, `loop=True`,
`show_controls=True`, `compress=False`. Pass `anim_style=AnimStyle(loop=False)`
to override only the fields you need — non-`None` fields are merged on top
of the defaults.

**Playback controls:** play/pause, scrub bar, speed (0.25×–2×), loop toggle.
Orbit controls remain active during playback — the viewer can rotate and zoom
while the animation plays. Title and annotation overlays are rendered in
animated exports (KaTeX math in labels and annotations is supported).

`export_animated_figure` also accepts a `style` `FigureStyle` parameter for
dimensions, background, and responsive layout.

# Standalone HTML Export

Self-contained HTML documents are the most portable export: open one by
double-clicking — no Python server required. Three.js still loads from CDN,
but all scene data and renderer modules are embedded inline.

## Static HTML

Export the current scene as a standalone `.html` file:

```python
viz = Visualizer()
viz(Point(1, 2, 3), color="#ff4444")
viz(Sphere(Point(0, 0, 0), radius=2), opacity=0.3)

viz.export_snapshot("scene.html")
```

The default path resolution is forgiving: relative paths resolve against the
current working directory, `~` expands to your home directory, missing parent
directories are created, and a missing extension is appended (`"scene"` →
`"scene.html"`). Pass `overwrite=True` to replace an existing file.

## Animated HTML

Record the scene's entity state during a Python animation loop, then embed the
recording as a self-contained HTML document with JS playback controls
(play/pause, scrub bar, speed 0.25×–2×, loop toggle):

```python
from pytanga.viz import AnimStyle

recording = viz.start_animation_recording()

for frame in range(90):
    p.entity = Point(...)     # update the entity in place
    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

viz.export_snapshot(
    "animated_scene.html",
    animation=recording,
    anim_style=AnimStyle(fps=30, loop=True),
)
```

Orbit controls stay active during playback, so viewers can rotate and zoom
while the animation runs. Title and annotation overlays are included (KaTeX
math in labels and annotations is supported).

### `AnimStyle`

Controls playback behaviour:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fps` | `int` | `30` | Playback frame rate |
| `loop` | `bool` | `True` | Loop the animation |
| `show_controls` | `bool` | `True` | Show play/pause/scrub controls |
| `compress` | `bool` | `False` | Gzip-compress embedded animation data (70–80 % smaller file) |

You only need to pass the fields you want to override — non-`None` fields are
merged on top of the exporter defaults.

## Figure Export (Presentations)

For embedding a scene in a slide deck or page, `export_figure()` produces an
HTML snippet (`<div>` + `<script type="module">`) rather than a full document —
no `<html>`, `<head>`, or global style resets:

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

Pass `path=None` to get the snippet back as a string instead of writing a file.
The same `animation=` + `anim_style=` combination works for animated figures:

```python
viz.export_figure(
    "animated_figure.html",
    animation=recording,
    style=FigureStyle(width=800, height=600, responsive=True),
    anim_style=AnimStyle(fps=30, loop=True),
)
```

### `FigureStyle`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | `int` | `800` | Canvas width in px |
| `height` | `int` | `600` | Canvas height in px |
| `background` | `str` | `"transparent"` | CSS background |
| `auto_rotate` | `bool` | `False` | Auto-rotate the camera |
| `show_title` | `bool` | `True` | Show the title overlay |
| `show_annotation` | `bool` | `True` | Show the annotation panel |
| `border_radius` | `str` | `"0"` | CSS border-radius |
| `responsive` | `bool` | `False` | Fill the parent container and resize with the window |

### Keyboard shortcuts in exported HTML

These shortcuts work in all exported HTML files (static, figure, and animated):

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` / `Cmd+S` | Download a PNG snapshot |
| `r` | Toggle camera auto-rotation |

## Open without saving

To preview the current scene as a standalone document without writing a file,
use `viz.open_snapshot()` — it writes the self-contained HTML to a temporary
file and opens it in a browser window.
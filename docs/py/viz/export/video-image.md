# Video & Image Export

Screenshots and video capture are different from the file exports: they
capture the **live browser viewport** via WebSocket, so the server must be
running (and a browser connected) for them to work. These capabilities
currently live on `SceneExporter`.

```python
from pytanga.viz import SceneExporter

exporter = SceneExporter(viz)
```

## Screenshots

**Browser shortcut:** `Ctrl+S` (or `Cmd+S` on macOS) downloads a PNG of the
current viewport.

**Programmatic screenshot** — requests the canvas over WebSocket and saves it
as PNG:

```python
exporter.screenshot("figure.png")
exporter.screenshot("figure_hd.png", width=1920, height=1080)
```

Screenshot captures the full viewport (including overlays such as labels,
title, and annotation); the browser-side `Ctrl+S` shortcut captures only the
WebGL canvas.

## Video Capture

Capture animation frames as sequenced PNGs, then stitch them into an MP4 with
`ffmpeg`:

```python
viz.show()  # start the server and open the browser

exporter.start_capture(width=800, height=600)

for frame in range(90):  # 3 seconds at 30 FPS
    viz.update_entity(point_id, Point(...))
    viz.flush()
    exporter.capture_frame()
    viz.sleep_ms(33)

exporter.finish_capture(video_path="orbit.mp4", fps=30)
```

### API

| Method | Purpose |
|--------|---------|
| `start_capture(*, folder, width, height)` | Begin a capture session (creates `folder`, or a temp dir if `None`) |
| `capture_frame(*, timeout)` | Capture a single sequenced PNG (`frame_0000.png`, …) |
| `finish_capture(*, video_path, fps, crf, keep_images, overwrite)` | Optionally encode MP4 and clean up temp frames |

### Requirements

- **`ffmpeg` must be installed and on your `PATH`** to produce a video. If it
  isn't, `finish_capture()` raises `RuntimeError`. (Skipping `video_path`
  still leaves the frame PNGs on disk and requires no `ffmpeg`.)
- The WebSocket server must be running (`viz.show()` / `viz.start_server()`).
- Temp folders are auto-cleaned after successful video creation unless
  `keep_images=True`; user-specified folders are never deleted.

### State machine

Capture follows `IDLE → CAPTURING → IDLE`. Invalid transitions (e.g. calling
`capture_frame()` before `start_capture()`, or `start_capture()` twice) raise
`RuntimeError`.
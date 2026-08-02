# Phase 15 — PNG Snapshots & MPEG Video Capture

**Prerequisites:** Phase 14 (SceneExporter refactored), Phase 7 (animation), Phase 11 (HTML export)

**Goal:** Add three screenshot/capture capabilities to the 3D viewer:

1. **Browser keyboard shortcut** (`Ctrl+S`) — user presses a key in the browser to download a PNG of the current viewport.
2. **Programmatic screenshot** (`SceneExporter.screenshot()`) — Python triggers a screenshot via WebSocket round-trip and saves the PNG to disk.
3. **Animation frame capture** — Python captures individual PNG frames during an animation loop, then optionally stitches them into an MP4 video using `ffmpeg`.

No headless browser, no playwright, no new Python dependencies beyond `ffmpeg` (system tool, checked via `shutil.which`). All capture goes through the live WebSocket connection.

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Use Cases

- **Manual screenshot:** User rotates the camera to a nice angle, presses `Ctrl+S`, gets a PNG.
- **Programmatic screenshot:** A script triggers `exporter.screenshot("figure.png", width=800, height=600)` and gets a PNG without any user interaction.
- **Animation recording:** A GA-driven animation runs in Python; each frame is captured as a PNG, then stitched into `animation.mp4` via ffmpeg.

### 1.2 Current State

- The `SceneExporter` class exists (Phase 14) with `export_html()`, `export_glb()`, `export_figure()`, `open_figure()`.
- The WebSocket pipeline already handles arbitrary JSON messages (`_send_raw()`).
- The server already processes incoming WebSocket messages in `_ws_handler()`.
- There is no mechanism to capture the browser's rendered viewport as an image.

### 1.3 Design Principles

1. **No headless browser, no playwright.** Capture is done through the live browser via WebSocket.
2. **`preserveDrawingBuffer: true`** is already in the WebGL renderer init (line 25 of `viewer.js`). The canvas supports `toDataURL()`.
3. **ffmpeg is optional.** Frame capture works without it (you get PNG sequences). Video stitching requires `ffmpeg` on the system PATH.
4. **Temp folders by default.** Animation frames go to `tempfile.mkdtemp()` and are cleaned up after video creation (unless the user opts to keep them).

---

## 2. Strategy A — Browser Keyboard Shortcut (`Ctrl+S`)

### 2.1 How It Works

- Add a `keydown` listener in `viewer.js` for `Ctrl+S` / `Cmd+S`.
- Prevent default browser save-dialog behavior.
- Call `renderer.domElement.toDataURL('image/png')` to capture the WebGL canvas.
- Trigger a browser download:
  ```js
  const link = document.createElement('a');
  link.download = `tanga_${timestamp}.png`;
  link.href = dataUrl;
  link.click();
  ```

### 2.2 Limitations

- `toDataURL()` on a WebGL canvas only captures the 3D scene — it does **not** include CSS2D overlays (labels, title, annotation panel) or fixed-position DOM elements. Those are rendered by the browser's layout engine, not WebGL.
- For a full-viewport capture including overlays, we would need `html2canvas` (CDN library). This is a potential future enhancement but adds a dependency.

### 2.3 What It Captures

| Element | Captured? |
|---------|-----------|
| 3D entities & operators | ✅ |
| Grid & axes helpers | ✅ |
| Background color | ✅ |
| CSS2D labels | ❌ (future: via html2canvas) |
| Title overlay (DOM) | ❌ |
| Annotation panel (DOM) | ❌ |
| Status indicator | ❌ |

### 2.4 Implementation

- **`viewer.js`:** Add ~15 lines in `initScene()` — a `keydown` event listener that checks for `Ctrl+S` and triggers `toDataURL()` + download.

---

## 3. Strategy B — Programmatic Screenshot (`SceneExporter.screenshot()`)

### 3.1 API

```python
# In SceneExporter (py/pytanga/viz/export/_exporter.py)

def screenshot(
    self,
    path: str | Path,
    *,
    width: int | None = None,
    height: int | None = None,
    timeout: float = 5.0,
) -> None:
    """Request a screenshot from the live viewer and save as PNG.

    Sends a ``{"type": "screenshot"}`` message over WebSocket.
    The browser captures its WebGL canvas and sends the base64-encoded
    PNG back.  Blocks up to *timeout* seconds waiting for the response.

    Requires the WebSocket server to be running
    (``viz.start()`` or ``viz.run()`` must have been called).

    Args:
        path: Output file path (e.g. ``"figure.png"``).
        width: Optional renderer width in pixels (resizes the canvas
            for this capture only).  ``None`` uses the current size.
        height: Optional renderer height in pixels.
        timeout: Maximum time to wait for the browser's response.

    Raises:
        RuntimeError: If the server is not running.
        TimeoutError: If the browser doesn't respond within *timeout*.
    """
```

### 3.2 WebSocket Protocol

**Python → Browser:**
```json
{"type": "screenshot"}
```

**Browser → Python:**
```json
{"type": "screenshot:data", "data": "data:image/png;base64,iVBORw0KGgo..."}
```

### 3.3 Implementation — Server Side

The server needs a way to receive the `screenshot:data` response and route it back to the waiting Python caller. The cleanest approach: use an `asyncio.Future`.

**`server.py` changes:**
- Add a `_pending_screenshots: dict[str, asyncio.Future]` dict keyed by a request ID.
- In `_ws_handler`, when a `screenshot:data` message arrives, resolve the matching future.
- Add a `request_screenshot() -> str` method that creates a request ID, sends `{"type": "screenshot", "request_id": "..."}`, creates a Future, and returns the awaitable.

**`SceneExporter.screenshot()`:**
- Check that `self._viz._server is not None` and `self._viz._loop is not None`.
- Schedule a coroutine on the server's event loop that:
  1. Calls `server.request_screenshot()` → awaits the Future.
  2. Decodes the base64 data.
  3. Writes the PNG to `path`.
- Blocks the calling thread with `concurrent.futures.wait()` or a threading `Event`.

### 3.4 Implementation — Browser Side

**`viewer.js` changes:**
- In `handleMessage()`, add a case for `"screenshot"`:
  ```js
  if (msg.type === 'screenshot') {
      const dataUrl = renderer.domElement.toDataURL('image/png');
      ws.send(JSON.stringify({
          type: 'screenshot:data',
          request_id: msg.request_id,
          data: dataUrl,
      }));
  }
  ```

### 3.5 Width/Height Override

If `width` and `height` are specified, the browser temporarily resizes the renderer, captures, and resizes back. This is done by including optional `width`/`height` in the screenshot message:

```json
{"type": "screenshot", "request_id": "abc", "width": 800, "height": 600}
```

---

## 4. Strategy C — Animation Frame Capture & MP4 Video

### 4.1 API: `SceneExporter.start_capture()` / `capture_frame()` / `finish_capture()`

A three-step workflow: start → capture frames → finish (optionally create video).

```python
# In SceneExporter

def start_capture(
    self,
    *,
    folder: str | Path | None = None,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Begin capturing frames to an image sequence.

    Creates *folder* (or a temporary directory if ``None``) and prepares
    a frame counter starting at 0.

    Args:
        folder: Directory to store frame PNGs.  If ``None``, a temporary
            directory is created (and cleaned up on :meth:`finish_capture`
            unless ``keep_images=True``).
        width: Renderer width for all frames.  ``None`` = current size.
        height: Renderer height for all frames.
    """


def capture_frame(self, *, timeout: float = 5.0) -> Path:
    """Capture a single frame and save it as a sequenced PNG.

    The frame is written to the capture folder as ``frame_0000.png``,
    ``frame_0001.png``, etc.  Returns the path to the written file.

    Blocks up to *timeout* seconds for the browser's response.
    """


def finish_capture(
    self,
    *,
    video_path: str | Path | None = None,
    fps: int = 30,
    crf: int = 23,
    keep_images: bool = False,
) -> Path | None:
    """Finish the frame capture and optionally create an MP4 video.

    Args:
        video_path: Output video path (e.g. ``"animation.mp4"``).
            If ``None``, no video is created — frames are left on disk.
        fps: Frame rate for the output video.
        crf: ffmpeg quality setting (0–51, lower = better, 23 = default).
        keep_images: If ``True``, the frame PNGs are kept after video
            creation.  If ``False`` (default), the capture folder is
            deleted after successful video encoding (only for temp folders).

    Returns:
        Path to the video file if *video_path* was given, otherwise ``None``.

    Raises:
        RuntimeError: If ``ffmpeg`` is not found on the system PATH.
    """
```

### 4.2 Usage Example

```python
from pytanga.viz import Visualizer, SceneExporter
from pytanga.geometry import Point
import math

viz = Visualizer()
viz.start()

point_id = viz.add(Point(3, 0, 0), color="#ff4444", size=0.15)
viz.flush()

exporter = SceneExporter(viz)

# Start capture — frames go to a temp folder
exporter.start_capture(width=800, height=600)

# Animation loop with frame capture
for frame in range(90):  # 3 seconds at 30 FPS
    angle = frame * 0.05
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    viz.update_entity(point_id, Point(x, y, 0))
    viz.flush()
    exporter.capture_frame()  # sends screenshot request, waits, saves PNG
    viz.sleep_ms(33)  # ~30 FPS

# Finish: create MP4, delete temp frames
exporter.finish_capture(video_path="orbit.mp4", fps=30)

viz.stop()
```

### 4.3 Frame File Naming

Frames are written as `frame_0000.png`, `frame_0001.png`, ... using zero-padded 4-digit numbers. This naming scheme is directly compatible with ffmpeg's `-i frame_%04d.png` pattern.

### 4.4 ffmpeg Command

```bash
ffmpeg -y -framerate 30 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 23 output.mp4
```

The `-y` flag overwrites existing files. The `-pix_fmt yuv420p` ensures compatibility with most video players.

### 4.5 Temp Folder Lifecycle

| Scenario | `folder` | `keep_images` | Behavior |
|----------|----------|---------------|----------|
| Temp, no video | `None` | N/A | Frames left on disk; user responsible for cleanup |
| Temp, with video | `None` | `False` (default) | Temp folder deleted after successful ffmpeg |
| Temp, with video | `None` | `True` | Temp folder kept; prints path to console |
| User folder, no video | `"my_frames/"` | N/A | Frames kept in user's folder |
| User folder, with video | `"my_frames/"` | `False` | Frames kept (user explicitly chose the folder) |
| User folder, with video | `"my_frames/"` | `True` | Frames kept |

**Rule:** `keep_images` only affects temp folders. User-specified folders are never deleted.

### 4.6 State Machine

```
IDLE  ──start_capture()──▶  CAPTURING
CAPTURING  ──capture_frame()──▶  CAPTURING  (increments counter)
CAPTURING  ──finish_capture()──▶  IDLE  (optional ffmpeg, optional cleanup)
```

- Calling `start_capture()` while already capturing raises `RuntimeError`.
- Calling `capture_frame()` or `finish_capture()` while not capturing raises `RuntimeError`.
- `finish_capture()` can be called without any frames (produces no video, just cleans up).

---

## 5. Files to Create / Modify

### 5.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/export/_screenshot.py` | `_request_screenshot(server) -> bytes` — sends screenshot request over WebSocket, awaits the base64 response, decodes to PNG bytes |
| `py/pytanga/viz/export/_capture.py` | `FrameCapture` class — manages the capture state machine (folder, counter), calls `_request_screenshot` per frame, runs ffmpeg |
| `py/tests/viz/test_phase15_screenshots.py` | Tests for screenshot protocol, frame naming, ffmpeg command generation |

### 5.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/export/_exporter.py` | Add `screenshot()`, `start_capture()`, `capture_frame()`, `finish_capture()` methods |
| `py/pytanga/viz/server.py` | Add `_pending_screenshots` dict; add `request_screenshot()` async method that creates a Future, sends the message, and awaits the response; handle `screenshot:data` in `_ws_handler` |
| `py/pytanga/viz/templates/viewer.js` | Add `Ctrl+S` keydown handler for browser shortcut; add `screenshot` message handler that calls `toDataURL()` and sends back `screenshot:data` |
| `py/pytanga/viz/__init__.py` | No new public exports needed (methods on `SceneExporter`) |

### 5.3 Files NOT Modified

- `py/pytanga/viz/visualizer.py` — unchanged
- `py/pytanga/viz/scene.py` — unchanged
- `py/pytanga/viz/serializer.py` — unchanged
- `py/pytanga/viz/_styles.py` — unchanged
- All JS renderer modules — unchanged
- `py/pytanga/viz/templates/viewer.html` — unchanged (but `preserveDrawingBuffer: true` should be verified)
- `py/pytanga/viz/templates/controls.js` — unchanged
- `py/pytanga/viz/templates/animator.js` — unchanged
- `py/pytanga/viz/export/_html.py` — unchanged
- `py/pytanga/viz/export/_figure_html.py` — unchanged
- `py/pytanga/viz/export/_gltf.py` — unchanged

---

## 6. WebSocket Protocol Extension

### 6.1 New Message Types

| Direction | Type | Fields | Purpose |
|-----------|------|--------|---------|
| Python → Browser | `screenshot` | `request_id`, `width?`, `height?` | Request a canvas capture |
| Browser → Python | `screenshot:data` | `request_id`, `data` (base64 data URL) | Response with the PNG |

### 6.2 Server-Side Future Resolution

```python
# In server.py

class VizServer:
    def __init__(self, ...):
        ...
        self._pending_screenshots: dict[str, asyncio.Future] = {}

    async def request_screenshot(self) -> bytes:
        """Send a screenshot request and return the PNG bytes."""
        import uuid
        request_id = uuid.uuid4().hex[:8]
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending_screenshots[request_id] = future

        await self._broadcast_raw(json.dumps({
            "type": "screenshot",
            "request_id": request_id,
        }))

        try:
            data_url = await asyncio.wait_for(future, timeout=5.0)
        finally:
            self._pending_screenshots.pop(request_id, None)

        # Strip the "data:image/png;base64," prefix and decode
        import base64
        _, b64 = data_url.split(",", 1)
        return base64.b64decode(b64)
```

In `_ws_handler`, add handling for incoming `screenshot:data`:

```python
elif msg_type == "screenshot:data":
    rid = data.get("request_id")
    if rid and rid in self._pending_screenshots:
        self._pending_screenshots[rid].set_result(data["data"])
```

### 6.3 Browser-Side Handler

```js
// In viewer.js handleMessage()

if (msg.type === 'screenshot') {
    const dataUrl = renderer.domElement.toDataURL('image/png');
    ws.send(JSON.stringify({
        type: 'screenshot:data',
        request_id: msg.request_id,
        data: dataUrl,
    }));
    return;
}
```

### 6.4 Threading Model

`SceneExporter` methods (`screenshot`, `capture_frame`) are called from the user's main thread, but the server's event loop runs in a background daemon thread. The flow is:

1. Main thread: `exporter.screenshot()` → schedules an `asyncio.run_coroutine_threadsafe()` call on the server's loop.
2. Server loop: The coroutine calls `server.request_screenshot()` → sends WebSocket message → awaits Future.
3. Browser: Receives `screenshot` → captures canvas → sends `screenshot:data`.
4. Server loop: `_ws_handler` receives `screenshot:data` → resolves Future → coroutine returns bytes.
5. Coroutine writes PNG to disk → signals completion via a `threading.Event`.
6. Main thread: Waits on the Event (with timeout) → returns.

---

## 7. Error Handling

| Error Condition | Behavior |
|-----------------|----------|
| Server not running | `RuntimeError("Server is not running. Call viz.start() or viz.run() first.")` |
| No browser connected | `RuntimeError("No browser connected. Open the viewer in a browser first.")` |
| Timeout waiting for response | `TimeoutError("Screenshot request timed out after {timeout}s")` |
| ffmpeg not found | `RuntimeError("ffmpeg not found on PATH. Install ffmpeg to create videos.")` |
| ffmpeg fails | `RuntimeError("ffmpeg exited with code {code}: {stderr}")` |
| `capture_frame()` outside capture | `RuntimeError("Not capturing. Call start_capture() first.")` |
| `start_capture()` while capturing | `RuntimeError("Already capturing. Call finish_capture() first.")` |
| `capture_frame()` with zero connected clients | Same as "No browser connected" — `RuntimeError` |

---

## 8. ffmpeg Detection

On `SceneExporter` import (or lazily on first `finish_capture()` call):

```python
import shutil

_FFMPEG_PATH = shutil.which("ffmpeg")

def _require_ffmpeg():
    if _FFMPEG_PATH is None:
        raise RuntimeError(
            "ffmpeg not found on PATH. Install ffmpeg to create videos:\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  macOS: brew install ffmpeg\n"
            "  Windows: choco install ffmpeg"
        )
```

---

## 9. Implementation Checklist

### 9.1 Browser Keyboard Shortcut

- [ ] **K1:** Add `keydown` event listener in `viewer.js` `initScene()` for `Ctrl+S` / `Cmd+S`
- [ ] **K2:** On `Ctrl+S`, call `renderer.domElement.toDataURL('image/png')`
- [ ] **K3:** Trigger browser download with filename `tanga_{YYYYMMDD}_{HHMMSS}.png`
- [ ] **K4:** Prevent default browser save-dialog behavior (`e.preventDefault()`)
- [ ] **K5:** Manual test: open viewer, press Ctrl+S → PNG downloads

### 9.2 Server-Side Screenshot Infrastructure

- [ ] **V1:** Add `self._pending_screenshots: dict[str, asyncio.Future]` to `VizServer.__init__`
- [ ] **V2:** Add `async request_screenshot(self) -> bytes` method to `VizServer`
- [ ] **V3:** In `_ws_handler`, handle incoming `screenshot:data` messages — resolve the matching Future
- [ ] **V4:** Handle timeout in `request_screenshot()` via `asyncio.wait_for`
- [ ] **V5:** Clean up pending futures on disconnect (in `_ws_handler` `finally` block)
- [ ] **V6:** Test: send screenshot request → browser responds → bytes decoded correctly

### 9.3 Browser Message Handler

- [ ] **B1:** Add `case "screenshot"` in `viewer.js` `handleMessage()` — call `toDataURL()`, send `screenshot:data` with `request_id`
- [ ] **B2:** Handle optional `width`/`height` in the screenshot message (temporary resize)
- [ ] **B3:** Test: Python sends screenshot request → browser responds with valid PNG data URL

### 9.4 `_screenshot.py` — Screenshot Request Helper

- [ ] **S1:** Create `py/pytanga/viz/export/_screenshot.py`
- [ ] **S2:** Implement `_request_screenshot(server, viz_loop) -> bytes` — schedules a coroutine on the server's event loop, waits for result via `threading.Event`
- [ ] **S3:** Decode base64 data URL to raw PNG bytes
- [ ] **S4:** Handle timeout with clear error message

### 9.5 `_capture.py` — Frame Capture State Machine

- [ ] **C1:** Create `py/pytanga/viz/export/_capture.py`
- [ ] **C2:** Implement `FrameCapture` class with `start()`, `capture()`, `finish()` methods
- [ ] **C3:** `start()` creates folder (temp or user-specified), initializes counter to 0
- [ ] **C4:** `capture()` calls `_request_screenshot()`, writes `frame_{counter:04d}.png`, increments counter
- [ ] **C5:** `finish()` optionally runs ffmpeg, optionally cleans up temp folder
- [ ] **C6:** Validate state transitions (can't capture before start, can't start twice)
- [ ] **C7:** ffmpeg command: `ffmpeg -y -framerate {fps} -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf {crf} {output}`
- [ ] **C8:** Run ffmpeg via `subprocess.run()`, capture stderr, check return code

### 9.6 `SceneExporter` Integration

- [ ] **E1:** Add `screenshot(path, *, width, height, timeout)` method
- [ ] **E2:** Add `start_capture(*, folder, width, height)` method — delegates to `FrameCapture`
- [ ] **E3:** Add `capture_frame(*, timeout) -> Path` method — delegates to `FrameCapture`
- [ ] **E4:** Add `finish_capture(*, video_path, fps, crf, keep_images) -> Path | None` — delegates to `FrameCapture`
- [ ] **E5:** Store `FrameCapture` instance as `self._capture`
- [ ] **E6:** All methods check that `self._viz._server is not None`

### 9.7 Tests

- [ ] **T1:** Test `FrameCapture` state machine — valid transitions, invalid transitions raise error
- [ ] **T2:** Test ffmpeg command generation (mock `subprocess.run`, verify correct args)
- [ ] **T3:** Test ffmpeg not found → `RuntimeError`
- [ ] **T4:** Test temp folder creation and cleanup (with and without `keep_images`)
- [ ] **T5:** Test user-specified folder is never deleted (even with `keep_images=False`)
- [ ] **T6:** Test `_request_screenshot` decoding of base64 data URL
- [ ] **T7:** Test `SceneExporter.screenshot()` raises if server not running
- [ ] **T8:** All existing tests pass (84 backend + 13 export = 97)

### 9.8 Smoke / Manual Verification

- [ ] **M1:** Open viewer, press Ctrl+S → PNG downloads to browser's default download folder
- [ ] **M2:** `exporter.screenshot("test.png")` → valid PNG file with correct content
- [ ] **M3:** `exporter.screenshot("test.png", width=1024, height=768)` → PNG at specified resolution
- [ ] **M4:** Frame capture with 30 frames → 30 PNGs in temp folder, correctly sequenced
- [ ] **M5:** `finish_capture(video_path="anim.mp4", fps=30)` → playable MP4 video
- [ ] **M6:** Temp folder deleted after video creation (when `keep_images=False`)
- [ ] **M7:** User-specified folder NOT deleted after video creation
- [ ] **M8:** `finish_capture()` without `video_path` → frames left on disk, no error
- [ ] **M9:** `exporter.screenshot()` with no browser connected → clear error message
- [ ] **M10:** Browser console has no errors

---

## 10. Verification Checklist

- [ ] Ctrl+S in browser downloads a PNG
- [ ] `SceneExporter.screenshot("path.png")` saves a valid PNG
- [ ] `start_capture()` + `capture_frame()` loop produces correctly sequenced PNGs
- [ ] `finish_capture(video_path=...)` produces a playable MP4 (if ffmpeg is available)
- [ ] `finish_capture(video_path=...)` raises clear error if ffmpeg is not available
- [ ] Temp folders are cleaned up by default after video creation
- [ ] User-specified folders are never deleted
- [ ] `keep_images=True` preserves frames even in temp folders
- [ ] Screenshot works at custom resolutions (width/height)
- [ ] Clear error messages for: server not running, no browser connected, timeout, ffmpeg missing
- [ ] State machine prevents invalid transitions (double start, capture before start, etc.)
- [ ] No regressions — all 97 existing tests still pass
- [ ] No circular imports introduced
- [ ] No new Python package dependencies (ffmpeg is a system tool)

---

## 11. Usage Examples

### 11.1 Manual Screenshot (Browser)
```
1. Open viewer (viz.run())
2. Rotate camera to desired angle
3. Press Ctrl+S
4. PNG downloads to browser's Downloads folder
```

### 11.2 Programmatic Screenshot
```python
from pytanga.viz import Visualizer, SceneExporter

viz = Visualizer()
viz.add(Point(1, 2, 3), color="#ff4444", size=0.15)
viz.start()

exporter = SceneExporter(viz)
exporter.screenshot("figure.png")  # captures current view
exporter.screenshot("figure_hd.png", width=1920, height=1080)

viz.stop()
```

### 11.3 Animation to MP4
```python
from pytanga.viz import Visualizer, SceneExporter
from pytanga.geometry import Point
import math

viz = Visualizer()
viz.start()

point_id = viz.add(Point(3, 0, 0), color="#ff4444", size=0.15)
viz.flush()

exporter = SceneExporter(viz)
exporter.start_capture(width=800, height=600)

for frame in range(90):
    angle = frame * 0.05
    viz.update_entity(point_id, Point(3 * math.cos(angle), 3 * math.sin(angle), 0))
    viz.flush()
    exporter.capture_frame()
    time.sleep(1/30)

exporter.finish_capture(video_path="orbit.mp4", fps=30, keep_images=False)
viz.stop()
```

### 11.4 Frame Sequence Only (No Video)
```python
exporter = SceneExporter(viz)
exporter.start_capture(folder="my_frames")  # explicit folder

for frame in range(100):
    viz.update_entity(...)
    viz.flush()
    exporter.capture_frame()

exporter.finish_capture()  # no video_path → frames stay in "my_frames/"
# Now run: ffmpeg -framerate 30 -i my_frames/frame_%04d.png -c:v libx264 output.mp4
```

---

## 12. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **14** | `SceneExporter` is the home for all new export methods |
| **7** | Animation frame streaming is the primary use case for frame capture |
| **11** | HTML export is unchanged (screenshots go through live WebSocket, not static HTML) |
| **13** | Figure export is complementary — `export_figure()` produces interactive HTML; `screenshot()` produces static PNG |
| **3** | Server WebSocket handler is extended for `screenshot:data` responses |
| **4** | `viewer.js` gains the `Ctrl+S` handler and `screenshot` message handler |
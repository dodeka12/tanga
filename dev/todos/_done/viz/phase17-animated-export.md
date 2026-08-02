# Phase 17 — Animated HTML Figure Export

**Prerequisites:** Phase 15 (screenshot + frame capture pipeline), Phase 13 (figure export), Phase 7 (animation)

**Goal:** Embed a self-contained, interactive **animated figure** in a static
HTML file. The user records entity state during their Python animation loop,
the state is serialized as a keyframe timeline into the HTML, and a JS
playback engine replays the animation with play/pause/scrub controls — all
without a running Python server.

**Status:** ✅ Complete (all 57+ checkboxes)


---

## 1. Motivation

### 1.1 Use Cases

- Share an animated geometric construction with a colleague who doesn't
  have `pytanga` installed. They open the HTML file in their browser and
  press Play.
- Embed an animated 3D figure in a presentation slide (reveal.js, Slidev)
  that plays on reveal.
- Publish a supplementary animated figure alongside a paper — the reader
  can scrub through the animation to understand the geometry.

### 1.2 Why Not Just Export MP4?

- MP4 is a passive format — fixed camera angle, no interaction.
- An HTML animation lets the viewer **rotate/pan/zoom** at any point
  while the animation plays. OrbitControls remain active during playback.
- The figure is self-contained — no server, no ffmpeg, no Python.

### 1.3 Design Goals

1. **Record from Python animation loop.** The user inserts one line:
   `recorder.record_frame()` into their existing `update_entity()`/`flush()` loop.

2. **Compact data.** Only dirty/changed entity fields are stored per frame.
   Stationary entities aren't re-serialized.

3. **Self-contained HTML output.** All entity meshes are created at load
   time from the initial frame. Subsequent frames update them in-place.

4. **JS playback engine.** `requestAnimationFrame`-driven player with:
   - Play / Pause toggle
   - Scrub bar (range slider)
   - Frame counter / time display
   - Speed control (0.25×, 0.5×, 1×, 2×)
   - Loop toggle

5. **Interactive camera.** OrbitControls work independently of playback —
   user can rotate while the animation plays.

6. **Backward compatible.** The existing `SceneExporter` keeps
   `export_figure()` for static figures. Animated export is a new method:
   `export_animated_figure()`.

---

## 2. Python API

### 2.1 Recording

```python
from pytanga.viz import Visualizer, SceneExporter
from pytanga.geometry import Point
import math, time

viz = Visualizer()
viz.start()

point_id = viz.add(Point(3, 0, 0), color="#ff4444", size=0.12)
viz.flush()

exporter = SceneExporter(viz)

# Start recording — captures every frame's entity state
recording = exporter.start_animation_recording()

# Animation loop — identical to frame capture, but for data not pixels
for frame in range(150):  # 5 seconds at 30 FPS
    angle = frame * 0.05
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    viz.update_entity(point_id, Point(x, y, 0))
    viz.flush()
    recording.capture_frame()  # records dirty entity state
    time.sleep(1/30)

# Export as self-contained animated HTML figure (snippet for embedding)
exporter.export_animated_figure(
    "animated_figure.html",
    recording,
    fps=30,
    loop=True,
    style=FigureStyle(width=800, height=600, responsive=True),
)

# Or export as full-page HTML document (full viewport, standalone)
exporter.export_animated_html(
    "animated_scene.html",
    recording,
    fps=30,
    loop=True,
    show_controls=True,
    compress=True,  # gzip the embedded frame data (~80% smaller)
)
viz.stop()
```

### 2.2 API: `start_animation_recording()` / `capture_frame()` / `export_animated_figure()`

```python
# In SceneExporter

def start_animation_recording(self) -> AnimationRecording:
    """Begin recording entity state for animated export.

    Returns an ``AnimationRecording`` context object used to capture
    per-frame entity state during the animation loop.
    """

def export_animated_figure(
    self,
    path: str | Path,
    recording: AnimationRecording,
    *,
    fps: int = 30,
    loop: bool = True,
    show_controls: bool = True,
    style: FigureStyle | None = None,
    overwrite: bool = False,
    compress: bool = False,
) -> None:
    """Export the recorded animation as an HTML snippet for embedding.

    The resulting file is a ``<div>`` + ``<script type="module">`` block
    — no ``<html>``, no ``<head>``, no global style resets.  Paste it
    directly into a reveal.js, Slidev, or Marp slide.

    This is the animated equivalent of ``SceneExporter.export_figure()``
    (Phase 13).  Use ``export_animated_html()`` for a full-page document
    instead.

    The resulting file contains:
      - The figure container (div + canvas + CSS2D labels)
      - The full entity state at every recorded frame
      - A JS playback engine with play/pause/scrub controls
      - Interactive orbit controls (rotate/pan/zoom during playback)

    Args:
        path: Output file path (e.g. ``"figure.html"``).
        recording: The ``AnimationRecording`` produced by
            ``start_animation_recording()``.
        fps: Playback frame rate.
        loop: Whether playback loops.
        show_controls: Whether to overlay play/pause/scrub controls.
        style: Optional ``FigureStyle`` for dimensions, background, etc.
            When not provided, uses canonical defaults (800×600,
            transparent bg).
        overwrite: If ``False``, raise on existing file.
        compress: If ``True``, gzip-compress the embedded animation JSON
            and embed a base64-encoded blob + ``DecompressionStream``-based
            JS decompressor.  Reduces file size by 70–80% for large
            animations at the cost of ~5 ms decompression at page load.
    """
```

### 2.3 `AnimationRecording` Class

```python
class AnimationRecording:
    """A sequence of entity state snapshots for animated export."""

    def __init__(self, scene: Scene) -> None:
        self._scene = scene
        self._frames: list[list[dict[str, Any]]] = []
        # _frames[i] = list of serialized entity dicts at frame i
        # Only dirty/visible entities at each frame

    def capture_frame(self) -> None:
        """Snapshot the current entity state.

        Only entities that are dirty since the last capture are included.
        This keeps the recording compact.
        """
        entities, _ = self._scene.flush(styles_map=...)
        if entities:
            self._frames.append(entities)

    @property
    def frames(self) -> list[list[dict[str, Any]]]:
        return self._frames

    @property
    def frame_count(self) -> int:
        return len(self._frames)
```

### 2.4 What `capture_frame()` Records

Each frame captures the **serialized entity dict** (same JSON format as
`serialize_entity()` produces for WebSocket messages):

```json
{
  "id": "abc123",
  "layer": "scene",
  "kind": "Point",
  "position": [2.5, 1.8, 0.0],
  "color": "#ff4444",
  "opacity": 1.0,
  "style": { "style_type": "PointStyle", "size": 0.12 }
}
```

For efficiency, only entities marked as `dirty` by `Scene.flush()` are
recorded. In a typical animation where one entity moves and the rest are
stationary, each frame contains only the moving entity's data — a few
hundred bytes.

### 2.5 Merged Data Structure for Export

Before export, frame data is merged into a compact format:

```json
{
  "initial_state": [
    // All entities at frame 0 (full serialization)
    { "id": "abc", "kind": "Point", "position": [3,0,0], ... },
    { "id": "def", "kind": "Sphere", "center": [0,0,0], "radius": 2.5, ... }
  ],
  "frames": [
    {
      "t": 0.0,
      "entities": [{ "id": "abc", "position": [3.0, 0.0, 0.0] }]
    },
    {
      "t": 0.033,
      "entities": [{ "id": "abc", "position": [2.95, 0.49, 0.0] }]
    },
    // ... one entry per recorded frame
  ],
  "fps": 30,
  "loop": true,
  "duration": 5.0
}
```

The `initial_state` is the full entity list (all properties present) used
to create all meshes. Each frame in `frames[]` only contains **changed
fields** — the JS playback engine applies them in-place via the same
`updateEntity()` / `inPlaceUpdate()` logic as the live viewer.

---

## 3. Embedded JS Playback Engine

### 3.1 What Goes Into the HTML

The exported HTML contains:

1. **Figure container** — same as Phase 13 static figure export (div + canvas + CSS2D).
2. **Initial entity state** — embedded as `window.__TANGA_ANIMATION__` JSON.
3. **Renderer modules** — the same stripped, concatenated JS modules from
   the static figure export (Point renderer, Sphere renderer, etc.).
4. **Playback engine** — a new JS module (~150 lines) that:
   - Reads `window.__TANGA_ANIMATION__`
   - Creates all meshes from `initial_state` via `createEntityMesh()`
   - Runs a `requestAnimationFrame` loop
   - Steps through frames based on elapsed time
   - Applies in-place updates (`position`, `opacity`, `color`, `scale`)
   - Handles structural changes (radius, kind) by full mesh rebuild
5. **Playback controls** — optional CSS-overlay UI with play/pause button,
   scrub bar, time display.

### 3.2 Playback Engine Logic

```js
// Animated figure playback engine

const animData = window.__TANGA_ANIMATION__;
const fps = animData.fps || 30;
const frames = animData.frames || [];
const initial = animData.initial_state || [];
const figMeshMap = new Map();

// State
let isPlaying = false;
let currentFrame = 0;
let startTime = 0;
let totalDuration = animData.duration || (frames.length / fps);

// Create all meshes from initial state
for (const ent of initial) {
    const mesh = createEntityMesh(ent);
    if (mesh) {
        figScene.add(mesh);
        figMeshMap.set(ent.id, mesh);
    }
}

// Playback loop (integrated into the existing render loop)
function _figAnimate(timestamp) {
    requestAnimationFrame(_figAnimate);

    if (isPlaying) {
        const elapsed = (timestamp - startTime) / 1000;
        if (animData.loop) {
            elapsed = elapsed % totalDuration;
        }
        const targetFrame = Math.floor(elapsed * fps);

        // Apply all frames from current to target
        for (let f = currentFrame + 1; f <= targetFrame && f < frames.length; f++) {
            for (const ent of frames[f].entities || []) {
                applyFrameUpdate(ent, figMeshMap);
            }
        }
        currentFrame = Math.min(targetFrame, frames.length - 1);

        // Stop at end if not looping
        if (elapsed >= totalDuration && !animData.loop) {
            isPlaying = false;
        }
    }

    figControls.update();
    figRenderer.render(figScene, figCamera);
    figLabelRenderer.render(figScene, figCamera);
    updateScrubBar();
}

function applyFrameUpdate(ent, meshMap) {
    const mesh = meshMap.get(ent.id);
    if (!mesh) return;

    // In-place position update
    if (ent.position) mesh.position.set(...ent.position);
    if (ent.center) mesh.position.set(...ent.center);
    if (ent.vector) {
        mesh.position.set(...(ent.origin || [0, 0, 0]));
        mesh.setRotationFromQuaternion(rotationFromDirection(...ent.vector));
    }

    // Opacity update
    if (ent.opacity !== undefined) {
        mesh.traverse(child => {
            if (child.material?.opacity !== undefined) {
                child.material.opacity = ent.opacity;
                child.material.transparent = ent.opacity < 1.0;
                child.material.depthWrite = ent.opacity >= 0.99;
                child.material.needsUpdate = true;
            }
        });
    }

    // Color update
    if (ent.color) {
        const c = new THREE.Color(ent.color);
        mesh.traverse(child => {
            if (child.material?.color) child.material.color.copy(c);
        });
    }

    // Scale update
    if (ent.scale) mesh.scale.set(...ent.scale);

    // Structural change → full rebuild
    if (ent.radius !== undefined || ent.extent !== undefined || 
        ent.kind !== undefined) {
        const oldLabels = mesh.userData._labels || [];
        removeEntityMesh(mesh);
        meshMap.delete(ent.id);
        const rebuilt = createEntityMesh({ ...mesh.userData.data, ...ent });
        if (rebuilt) {
            figScene.add(rebuilt);
            meshMap.set(ent.id, rebuilt);
            for (const lblId of oldLabels) {
                // re-attach labels (tracked via userData._labels)
            }
        }
    }
}
```

### 3.3 Playback Controls (CSS Overlay)

```html
<div class="tanga-playback-controls" style="
    position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%);
    display: flex; gap: 8px; align-items: center;
    background: rgba(0,0,0,0.7); padding: 6px 12px; border-radius: 6px;
    z-index: 10; pointer-events: auto;
    color: #ccc; font-family: sans-serif; font-size: 12px;
">
    <button id="tanga-play-btn" style="background:none;border:1px solid #666;color:#ccc;
        border-radius:3px;padding:2px 8px;cursor:pointer;">▶ Play</button>
    <input type="range" id="tanga-scrub" min="0" max="150" value="0"
        style="width:150px; cursor:pointer;">
    <span id="tanga-time">0.0s / 5.0s</span>
    <select id="tanga-speed" style="background:#222;color:#ccc;border:1px solid #666;
        border-radius:3px;padding:2px 4px;">
        <option value="0.25">0.25×</option>
        <option value="0.5">0.5×</option>
        <option value="1" selected>1×</option>
        <option value="2">2×</option>
    </select>
    <label style="cursor:pointer;">
        <input type="checkbox" id="tanga-loop" checked> Loop
    </label>
</div>
```

Controls logic:
- **Play/Pause:** Toggles `isPlaying`, sets/resets `startTime`.
- **Scrub bar:** Maps frame index to slider position. Scrubbing sets
  `currentFrame` and applies all frames from 0 to the scrubbed index.
- **Time display:** Shows `currentFrame / fps` seconds.
- **Speed:** Multiplier on the elapsed time calculation.
- **Loop:** Controls `animData.loop` at runtime.

---

## 4. Data Size Considerations

### 4.1 Compact Frame Encoding

For a typical animation with 3 entities (one moving, two stationary) at
30 FPS for 5 seconds (150 frames):

- `initial_state`: ~2-3 KB (full serialization of 3 entities + labels)
- Each frame: ~50-100 bytes (only the position field of the moving entity)
- Total frames: 150 × 80 bytes ≈ **12 KB**
- Total embedded JSON: **~15 KB** + renderer modules (~40 KB) + Three.js CDN

Total HTML file: **~60 KB** (without Three.js, which loads from CDN).

For 10 moving entities: ~150 × 800 bytes ≈ **120 KB** frame data.

### 4.2 Optional: Gzip Compression of Embedded JSON

For large animations (100+ frames, many entities), the embedded JSON data
can be gzip-compressed at export time and decompressed in the browser at
page load via the **`DecompressionStream` API** (supported in Chrome 80+,
Firefox 113+, Safari 16.4+).

**Python side (export time):**
```python
import gzip, base64, json

if compress:
    raw_json = json.dumps(anim_data, separators=(",", ":")).encode("utf-8")
    compressed = base64.b64encode(gzip.compress(raw_json)).decode("ascii")
    # Embed as:
    # <script type="application/octet-stream" id="tanga-anim-data">
    #   H4sIAAAAAAAC/...
    # </script>
```

**JS side (page load):**
```js
const b64 = document.getElementById("tanga-anim-data").textContent.trim();
const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
const ds = new DecompressionStream("gzip");
const writer = ds.writable.getWriter();
writer.write(bytes);
writer.close();
const reader = ds.readable.getReader();
const chunks = [];
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
}
const decompressed = new TextDecoder().decode(
    new Uint8Array(chunks.flatMap(c => [...c]))
);
const animData = JSON.parse(decompressed);
```

**Trade-off:**

| Approach | File Size (300 frames, 10 entities) | Page Load Overhead |
|----------|-------------------------------------|---------------------|
| Plain JSON embedded | ~400 KB | 0 ms |
| Gzip-compressed inline | ~80 KB | ~5 ms decompression on load + ~20 lines JS |

The `compress=True` option is opt-in — default is uncompressed (simpler
implementation, faster page load for small animations).

### 4.3 Optimization: Key-Value Delta Frames

Instead of serializing full entity dicts per frame, store only the changed
fields. The recording already does this via `Scene.flush()` which only
marks dirty entities. The JSON output can be further compressed:

```json
{
  "frames": [
    null,                         // frame 0: use initial_state
    null,                         // frame 1: no changes
    ["abc", "p", [2.95, 0.49, 0]],  // frame 2: entity "abc", field "p" (position)
    null,                         // frame 3: no changes
    // ...
  ],
  "field_map": { "p": "position", "o": "opacity", "c": "center" }
}
```

This is an optional optimization for later. The initial implementation
uses the straightforward JSON format.

---

## 5. Files to Create / Modify

### 5.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/export/_animation_recording.py` | `AnimationRecording` class — captures per-frame entity state, stores it for export |
| `py/pytanga/viz/export/_animated_figure.py` | `render_export_animated_figure()` and `render_export_animated_html()` — generate the animated HTML snippet and full-page document respectively |
| `py/tests/viz/test_phase17_animated_export.py` | Tests for recording, frame serialization, HTML generation |

### 5.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/export/_exporter.py` | Add `start_animation_recording()`, `export_animated_figure()`, `export_animated_html()` methods |
| `py/pytanga/viz/__init__.py` | Export `AnimationRecording` (if users need the type) |

### 5.3 Files NOT Modified

- `py/pytanga/viz/visualizer.py` — unchanged
- `py/pytanga/viz/scene.py` — unchanged (recording uses existing `flush()`)
- `py/pytanga/viz/serializer.py` — unchanged (recording uses existing serialization)
- All JS renderer modules — unchanged
- `py/pytanga/viz/templates/viewer.html` / `viewer.js` — unchanged
- `py/pytanga/viz/export/_figure_html.py` — baseline for the animated variant
- `py/pytanga/viz/export/_html.py` — unchanged

---

## 6. Implementation Checklist

### 6.1 `_animation_recording.py` (new)

- [ ] **R1:** Create `py/pytanga/viz/export/_animation_recording.py`
- [ ] **R2:** Implement `AnimationRecording.__init__(scene, styles_map)`
- [ ] **R3:** `capture_frame()` calls `scene.flush(styles_map=...)` and stores dirty entities
- [ ] **R4:** `frames` property returns the list of frame snapshots
- [ ] **R5:** `frame_count` property returns length
- [ ] **R6:** `get_initial_state()` returns full state from `scene.full_state()`
- [ ] **R7:** `to_json(compress=False)` serializes the recording to a compact JSON-serializable dict; when `compress=True`, returns the gzip-compressed base64 blob as a string for direct embedding

### 6.2 `_animated_figure.py` (new)

- [ ] **A1:** Create `py/pytanga/viz/export/_animated_figure.py`
- [ ] **A2:** Implement `render_export_animated_figure(recording, figure_style, figure_config) -> str` — HTML snippet (``<div>`` + ``<script>``, no ``<html>``/``<head>``/``<body>``)
- [ ] **A2b:** Implement `render_export_animated_html(recording, scene_config, show_controls, compress) -> str` — full-page document (``<!DOCTYPE html>``, ``<html>``, ``<head>``, ``<body>``), canvas fills viewport
- [ ] **A3:** Output format (both): CDN script tags + embedded animation JSON + `<script type="module">` with renderer modules + playback engine
- [ ] **A4:** Embed `initial_state` and `frames[]` as `window.__TANGA_ANIMATION__` (plain JSON, or gzip-compressed base64 blob if `compress=True`)
- [ ] **A4b:** When `compress=True`, embed the decompression bootstrapper JS (see §4.2) after the `<script>` tag carrying the compressed data
- [ ] **A5:** Inline stripped renderer modules (same `_strip_imports` logic as static figure export)
- [ ] **A6:** Inline the playback engine JS (~150 lines):
  - [ ] Mesh creation from `initial_state`
  - [ ] Frame stepping via `requestAnimationFrame`
  - [ ] In-place entity updates (`position`, `center`, `opacity`, `color`, `scale`)
  - [ ] Structural change handling (radius, extent, kind → full rebuild)
  - [ ] Label tracking (re-attach after rebuild via `userData._labels`)
  - [ ] Loop logic
- [ ] **A7:** Inline playback controls HTML + JS (when `show_controls=True`):
  - [ ] Play/Pause button
  - [ ] Scrub bar (range input)
  - [ ] Time display
  - [ ] Speed selector
  - [ ] Loop checkbox
- [ ] **A8:** `render_export_animated_figure()`: respect `FigureStyle` (dimensions, background, auto_rotate, responsive)
- [ ] **A8b:** `render_export_animated_html()`: respect `SceneConfig` (background, grid, axes, camera); renderer fills `window.innerWidth/Height`

### 6.3 `_exporter.py`

- [ ] **E1:** Add `start_animation_recording() -> AnimationRecording` method
- [ ] **E2:** Add `export_animated_figure(path, recording, *, fps, loop, show_controls, style, overwrite, compress)` method
- [ ] **E3:** Add `export_animated_html(path, recording, *, fps, loop, show_controls, scene_config, overwrite, compress)` method
- [ ] **E4:** `start_animation_recording()` initializes and returns an `AnimationRecording` from the current scene
- [ ] **E5:** Both export methods check recording is not empty, generate HTML, write to path

### 6.4 `__init__.py`

- [ ] **I1:** Export `AnimationRecording` (optional — users may not need to reference the type)

### 6.5 Tests

- [ ] **T1:** Test `AnimationRecording.capture_frame()` stores dirty entities
- [ ] **T2:** Test `AnimationRecording.frames` is empty before any capture
- [ ] **T3:** Test `AnimationRecording.get_initial_state()` returns full entity list
- [ ] **T4:** Test `AnimationRecording.to_json()` produces valid structure with `initial_state`, `frames[]`, `fps`
- [ ] **T4b:** Test `AnimationRecording.to_json(compress=True)` produces a base64-encoded gzip blob that decompresses to valid JSON
- [ ] **T5:** Test `export_animated_figure()` creates a valid HTML snippet (no `<html>`, `<head>`, `<body>`)
- [ ] **T5b:** Test `export_animated_html()` creates a valid full-page HTML document (`<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`)
- [ ] **T6:** Test exported HTML (both) contains `window.__TANGA_ANIMATION__`
- [ ] **T7:** Test exported HTML (both) contains `<script type="module">` with playback engine
- [ ] **T8:** Test exported HTML includes play/pause controls when `show_controls=True`
- [ ] **T9:** Test exported HTML excludes controls when `show_controls=False`
- [ ] **T10:** All existing tests pass (493)

### 6.6 Manual Verification

- [ ] **M1:** Create an animated figure (snippet) with 3 moving entities → paste into a reveal.js slide → press Play → animation runs in the slide
- [ ] **M1b:** Create an animated HTML (full-page) with 3 moving entities → double-click to open → press Play → animation runs full viewport
- [ ] **M2:** Rotate camera while animation plays — orbit controls work independently
- [ ] **M3:** Scrub bar: drag to mid-point → entities jump to mid-frame state
- [ ] **M4:** Speed control: set to 2× → animation plays twice as fast
- [ ] **M5:** Loop: end of animation → restarts from beginning
- [ ] **M6:** Labels follow their animated parent entities
- [ ] **M7:** Structural changes (sphere wireframe on/off, point size change) trigger rebuild and re-attach labels
- [ ] **M8:** Figure respects `responsive=True` and fills the browser window
- [ ] **M9:** Browser console has no errors
- [ ] **M10:** Exported file works when opened from a different directory/machine (CDN-only deps)
- [ ] **M11:** `compress=True` export: browser decompresses gzip blob automatically, animation plays identically to uncompressed version
- [ ] **M12:** `compress=True` export: page load time is not noticeably affected (decompression < 10 ms)

---

## 7. Verification Checklist

- [ ] `start_animation_recording()` returns an `AnimationRecording`
- [ ] `capture_frame()` snapshots dirty entities via `Scene.flush()`
- [ ] `export_animated_figure()` generates valid HTML
- [ ] Embedded JSON contains `initial_state` and `frames[]`
- [ ] Playback engine creates all meshes from `initial_state`
- [ ] Playback engine applies in-place updates per frame
- [ ] Playback engine handles structural changes (radius, extent, kind)
- [ ] Playback engine respects `loop` setting
- [ ] Play/Pause, scrub, speed, loop controls work
- [ ] OrbitControls work during playback
- [ ] Labels track animated parent entities
- [ ] Responsive layout works when `FigureStyle(responsive=True)`
- [ ] Exported file works offline (after CDN load)
- [ ] No Python server needed for playback
- [ ] All existing tests pass (493)

---

## 8. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **13** | Static figure export is the baseline — animated export builds on the same renderer modules, container layout, and `FigureStyle`/`FigureConfig` |
| **15** | Screenshot/frame capture is complementary — MP4 video is a different output format for the same recording data |
| **7** | Animation system (tweens, timeline, in-place updates) is the JS inspiration — animated export reuses the `inPlaceUpdate`/`updateEntity` logic |
| **16** | Not implemented — off-screen capture is replaced by the simpler live-viewport approach |

---

## 9. Usage Example

```python
from pytanga.viz import Visualizer, SceneExporter
from pytanga.geometry import Point, Sphere
import math

viz = Visualizer()
viz.start()

# Setup scene
s1 = viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ff4444", opacity=0.3, label="S₁")
s2 = viz.add(Sphere(Point(3, 0, 0), 1.3), color="#4488ff", opacity=0.3, label="S₂")
viz.flush()

exporter = SceneExporter(viz)

# Record animation
recording = exporter.start_animation_recording()

for frame in range(90):  # 3 seconds at 30 FPS
    x = 3.0 * math.sin(frame * 0.08)
    viz.update_entity(s2, Sphere(Point(x, 0, 0), 1.3))
    viz.flush()
    recording.capture_frame()

# Export as self-contained animated HTML figure
exporter.export_animated_figure(
    "sphere_animation.html",
    recording,
    fps=30,
    loop=True,
    style=FigureStyle(width=800, height=600, responsive=True),
)

viz.stop()
print("Done. Open sphere_animation.html in a browser.")
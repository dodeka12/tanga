# Phase 16 — Off-Screen Rendering & DOM-Integrated Capture

**Prerequisites:** Phase 15 (screenshot + frame capture pipeline)

**Goal:** Replace the Phase 15 screenshot handler with an **off-screen renderer**
that captures WebGL content without resizing the visible viewport.  Integrate
**html2canvas** so that DOM overlays (labels, title, annotation panel) are
composited into the final PNG.  The off-screen renderer mirrors the on-screen
camera so that user interactions (rotate, pan, zoom) appear in captured frames.

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Current Problems (Phase 15)

1. **Visible viewport resize** — `renderer.setSize(width, height)` shrinks the
   on-screen render area to the capture dimensions.  The user sees a tiny
   viewport during animation capture.

2. **No DOM overlays in capture** — `renderer.domElement.toDataURL()` only
   captures the WebGL canvas.  Labels (CSS2D), the title overlay, and the
   markdown annotation panel are invisible in screenshots and video frames.

3. **Restore flicker** — After `finish_capture()`, the `restore_size` message
   triggers `onResize()` which jumps the renderer back to full viewport.  This
   causes a visible flash.

### 1.2 Design Goals

1. **Off-screen renderer** — A second `WebGLRenderer` attached to an invisible
   `<canvas>` (never appended to the DOM).  On each `screenshot` request, this
   renderer renders the **same** `scene` and **a clone** of the on-screen
   camera at the target resolution.  The visible viewport is untouched.

2. **DOM overlay capture via html2canvas** — After rendering the WebGL layer,
   `html2canvas(document.body)` captures the full DOM tree (including the
   off-screen canvas, labels, title, annotation).  The result is composited
   at the target resolution.

3. **Camera mirroring** — The off-screen renderer uses a `PerspectiveCamera`
   that copies `.position`, `.quaternion`, `.fov`, `.near`, `.far` from the
   on-screen `controls` camera each frame.  User pans/rotates/zooms are
   reflected in captured frames.

4. **CSS2D label capture** — `html2canvas` natively renders CSS-styled `<div>`
   elements that Three.js's `CSS2DRenderer` positions.  However the CSS2D
   positions depend on the screen-space projection of the on-screen camera at
   the on-screen resolution.  To get labels positioned correctly at the capture
   resolution, we temporarily:
   - Set the CSS2DRenderer to the off-screen canvas size
   - Call `css2DRenderer.render(scene, offscreenCamera)` to recalculate label DOM positions
   - Run `html2canvas`
   - Restore the CSS2DRenderer to the on-screen size

5. **Zero visible impact** — The browser window, on-screen renderer, and DOM
   layout remain at full viewport throughout the entire capture session.  No
   resize flicker, no `restore_size` message needed.

---

## 2. Technical Approach

### 2.1 Off-Screen Renderer

Created once on page load (in `viewer.js` `initScene()`):

```js
const offscreenCanvas = document.createElement('canvas');
const offscreenRenderer = new THREE.WebGLRenderer({
    canvas: offscreenCanvas,
    antialias: true,
    alpha: true,
    preserveDrawingBuffer: true,
});
offscreenRenderer.setPixelRatio(1);  // exact pixel control, no device scaling
// Never append offscreenCanvas to the DOM — it stays invisible
```

On each screenshot request:

```js
// 1. Clone the on-screen camera's state into a temporary camera
const offscreenCamera = new THREE.PerspectiveCamera(
    camera.fov,           // copied from live camera
    width / height,       // capture aspect ratio
    camera.near,
    camera.far,
);
offscreenCamera.position.copy(camera.position);
offscreenCamera.quaternion.copy(camera.quaternion);

// 2. Render scene off-screen at target resolution
offscreenRenderer.setSize(width, height);
offscreenRenderer.render(scene, offscreenCamera);

// 3. Capture the off-screen canvas → data URL
const dataUrl = offscreenCanvas.toDataURL('image/png');
```

This is ~15 lines. The visible renderer is never touched.

### 2.2 html2canvas for DOM Overlays

Added as a classic `<script>` tag in `viewer.html`:

```html
<script src="https://unpkg.com/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
```

**Why `unpkg.com`:** Same CDN as `marked` — consistent provider, zero new
origins, tiny library (~30KB minified).

On each screenshot request, after rendering the off-screen WebGL layer:

```js
// Temporarily point CSS2DRenderer at the off-screen canvas so label
// positions are calculated at the capture resolution + aspect ratio.
const origLabelSize = { w: window._labelRenderer.domElement.width, h: window._labelRenderer.domElement.height };
window._labelRenderer.setSize(width, height);
window._labelRenderer.render(scene, offscreenCamera);

// Capture the full DOM (includes the off-screen <canvas> + labels + title + annotation)
const domCanvas = await html2canvas(document.body, {
    width: width,
    height: height,
    backgroundColor: null,  // transparent
    scale: 1,               // exact pixels (no DPI scaling)
});

// Restore CSS2D renderer to on-screen size
window._labelRenderer.setSize(origLabelSize.w, origLabelSize.h);

// Composite: draw WebGL canvas onto DOM canvas background
// Since html2canvas already captured the off-screen canvas (it's in the DOM
// as a child element), the off-screen canvas content may already be embedded.
// If not, draw it manually:
const ctx = domCanvas.getContext('2d');
ctx.globalCompositeOperation = 'destination-over';
ctx.drawImage(offscreenCanvas, 0, 0, width, height);

const dataUrl = domCanvas.toDataURL('image/png');
```

### 2.3 Label Position Recalculation

The CSS2DRenderer projects 3D positions to 2D screen coordinates based on the
camera and renderer size.  To get labels positioned correctly at the capture
resolution:

1. Temporarily set `window._labelRenderer.setSize(width, height)`
2. Call `window._labelRenderer.render(scene, offscreenCamera)` — this updates
   the CSS `transform` of each label's DOM element
3. Run `html2canvas` — labels are now at their capture-resolution positions
4. Restore `window._labelRenderer.setSize(originalWidth, originalHeight)` and
   call `window._labelRenderer.render(scene, camera)` to restore

### 2.4 Compositing Strategy

`html2canvas(document.body)` already captures the off-screen `<canvas>` because
it's a DOM child (appended somewhere, or referenced by `offscreenRenderer`).
Since we don't append it to the DOM, we need to manually composite:

**Approach:** Keep the off-screen canvas invisible.  After `html2canvas`
captures the DOM layer (title, annotation, labels), composite the WebGL
layer underneath:

```js
// 1. Capture DOM layer (title, annotation, labels)
//    Use html2canvas on a wrapper that excludes the main WebGL canvas
const domCanvas = await html2canvas(document.getElementById('overlay-root'), {
    backgroundColor: null, width, height, scale: 1,
});

// 2. Create final composite canvas
const finalCanvas = document.createElement('canvas');
finalCanvas.width = width;
finalCanvas.height = height;
const ctx = finalCanvas.getContext('2d');

// 3. Draw WebGL off-screen canvas as background
ctx.drawImage(offscreenCanvas, 0, 0, width, height);

// 4. Draw DOM overlay canvas on top
ctx.drawImage(domCanvas, 0, 0, width, height);

const dataUrl = finalCanvas.toDataURL('image/png');
```

**Alternative (simpler):** Temporarily wrap the on-screen `renderer.domElement`
with `display: none` via CSS, append the off-screen canvas to `document.body`
(making it visible to `html2canvas`), capture, then swap back.  This is
more reliable because `html2canvas` renders whatever is in the DOM.

### 2.5 Recommended Implementation Strategy

1. Append the off-screen canvas to `document.body` with `style="position:fixed;top:0;left:0;z-index:-1;width:1px;height:1px;"` (always present but effectively invisible).
2. On screenshot: set off-screen canvas size to `width`×`height` via CSS, temporarily hide the main `renderer.domElement` (`display:none`), run CSS2D render at capture size, call `html2canvas(document.body)`, restore.
3. This way `html2canvas` naturally includes the off-screen canvas as any other DOM element.

---

## 3. Simplified Screenshot Handler

Replaces the current `case 'screenshot'` block in `viewer.js`:

```js
} else if (msg.type === 'screenshot') {
    const w = msg.width || renderer.domElement.width;
    const h = msg.height || renderer.domElement.height;

    // ── 1. Clone camera ──
    const offscreenCamera = camera.clone();
    offscreenCamera.aspect = w / h;
    offscreenCamera.updateProjectionMatrix();

    // ── 2. Render off-screen WebGL layer ──
    offscreenRenderer.setSize(w, h);
    offscreenRenderer.render(scene, offscreenCamera);

    // ── 3. Position CSS2D labels at capture resolution ──
    const origLS = { w: window._labelRenderer.domElement.width, h: window._labelRenderer.domElement.height };
    window._labelRenderer.setSize(w, h);
    window._labelRenderer.render(scene, offscreenCamera);

    // ── 4. Swap canvases in DOM for html2canvas capture ──
    const mainCanvas = renderer.domElement;
    mainCanvas.style.display = 'none';
    offscreenCanvas.style.width = w + 'px';
    offscreenCanvas.style.height = h + 'px';
    offscreenCanvas.style.position = 'fixed';
    offscreenCanvas.style.top = '0';
    offscreenCanvas.style.left = '0';
    offscreenCanvas.style.zIndex = '-1';
    if (!offscreenCanvas.parentNode) document.body.appendChild(offscreenCanvas);

    // ── 5. Capture full DOM (WebGL + overlays) ──
    html2canvas(document.body, { width: w, height: h, backgroundColor: null, scale: 1 })
        .then(domCanvas => {
            // Restore on-screen state
            mainCanvas.style.display = '';
            offscreenCanvas.style.width = '1px';
            offscreenCanvas.style.height = '1px';
            window._labelRenderer.setSize(origLS.w, origLS.h);

            const dataUrl = domCanvas.toDataURL('image/png');
            ws.send(JSON.stringify({
                type: 'screenshot:data',
                request_id: msg.request_id,
                data: dataUrl,
            }));
        });
}
```

---

## 4. Removed from Phase 15

The following Phase 15 artifacts are **removed**:

| Artifact | Reason |
|----------|--------|
| `renderer.setSize()` in screenshot handler | Replaced by off-screen renderer |
| `camera.aspect = w/h` in screenshot handler | Off-screen camera clones the live camera |
| `restore_size` message type | No longer needed — visible renderer is never resized |
| `restore_size` handling in `handleMessage()` | Removed |
| `restore_size` sending in `finish_capture()` | Removed |

### What Moves to Camera Clone

- `camera.position.copy(camera.position)` — copies live camera position
- `camera.quaternion.copy(camera.quaternion)` — copies live camera orientation
- `camera.fov` — used directly in `PerspectiveCamera` constructor
- Controls (`OrbitControls`) automatically update the live `camera` — the clone inherits this each frame

---

## 5. Files to Modify

| File | Changes |
|------|---------|
| `py/pytanga/viz/templates/viewer.html` | Add `<script src="https://unpkg.com/html2canvas@1.4.1/dist/html2canvas.min.js">` |
| `py/pytanga/viz/templates/viewer.js` | Replace screenshot handler with off-screen renderer + html2canvas composite; remove `restore_size` handler; add off-screen renderer/canvas setup in `initScene()` |
| `py/pytanga/viz/export/_exporter.py` | Remove `restore_size` sending from `finish_capture()` |

### Files NOT Modified

- `py/pytanga/viz/server.py` — unchanged (screenshot protocol is the same)
- `py/pytanga/viz/export/_screenshot.py` — unchanged
- `py/pytanga/viz/export/_capture.py` — unchanged
- `py/pytanga/viz/visualizer.py` — unchanged
- `py/pytanga/viz/scene.py` — unchanged
- All JS renderer modules — unchanged

---

## 6. Dependencies

| Layer | Dependency | Purpose |
|-------|-----------|---------|
| Browser | `html2canvas` ^1.4 | DOM → canvas rendering (CDN, ~30KB) |

Loaded from `https://unpkg.com/html2canvas@1.4.1/dist/html2canvas.min.js`
(same CDN provider as `marked`).

---

## 7. What's Captured

| Element | Phase 15 | Phase 16 |
|---------|----------|----------|
| 3D entities & operators | ✅ | ✅ |
| Grid & axes helpers | ✅ | ✅ |
| Background color | ✅ | ✅ |
| CSS2D labels | ❌ | ✅ |
| Title overlay (DOM) | ❌ | ✅ |
| Annotation panel (DOM) | ❌ | ✅ |
| Status indicator | ❌ | ✅ |

---

## 8. Implementation Checklist

### 8.1 HTML Dependency

- [ ] **H1:** Add `<script src="https://unpkg.com/html2canvas@1.4.1/dist/html2canvas.min.js">` to `viewer.html` (in `<head>`, alongside `marked`)

### 8.2 Off-Screen Renderer Setup

- [ ] **R1:** Create off-screen `<canvas>` and `WebGLRenderer` in `viewer.js` `initScene()`
- [ ] **R2:** Set `preserveDrawingBuffer: true` and `setPixelRatio(1)` on off-screen renderer
- [ ] **R3:** Append off-screen canvas to `document.body` with minimal dimensions and hidden z-index

### 8.3 Screenshot Handler Rewrite

- [ ] **S1:** Clone on-screen camera (`clone()`, set aspect, update projection) for off-screen render
- [ ] **S2:** Render scene to off-screen renderer at requested width/height
- [ ] **S3:** Temporarily set CSS2DRenderer size to capture dimensions, call `.render()` to reposition labels
- [ ] **S4:** Temporarily swap main canvas (display:none) and off-screen canvas in DOM
- [ ] **S5:** Call `html2canvas(document.body)` with capture dimensions, `backgroundColor: null`, `scale: 1`
- [ ] **S6:** Restore main canvas, off-screen canvas size, and CSS2DRenderer after capture
- [ ] **S7:** Send composite data URL as `screenshot:data` response

### 8.4 Cleanup — Remove Old Code

- [ ] **C1:** Remove `renderer.setSize(w, h)` from screenshot handler
- [ ] **C2:** Remove `camera.aspect = w/h` from screenshot handler
- [ ] **C3:** Remove `restore_size` case from `handleMessage()` in `viewer.js`
- [ ] **C4:** Remove `restore_size` sending from `SceneExporter.finish_capture()` in `_exporter.py`

### 8.5 Manual Verification

- [ ] **M1:** `exporter.screenshot("test.png", width=800, height=600)` — visible viewport unchanged
- [ ] **M2:** Labels visible in PNG at correct 3D positions
- [ ] **M3:** Title overlay visible in PNG at top center
- [ ] **M4:** Annotation panel (if set) visible in PNG at bottom
- [ ] **M5:** User rotates camera with mouse → next screenshot reflects the new angle
- [ ] **M6:** Animation frame capture produces non-black video frames
- [ ] **M7:** `finish_capture()` does not resize visible viewport
- [ ] **M8:** No console errors in browser
- [ ] **M9:** All 97 existing tests pass

---

## 9. Verification Checklist

- [ ] Off-screen renderer created at page load (one-time cost)
- [ ] Screenshot handler uses off-screen renderer exclusively
- [ ] Visible viewport never changes during capture
- [ ] Camera clone mirrors live camera (position, quaternion, fov)
- [ ] CSS2D labels appear at correct positions in captured frames
- [ ] Title and annotation overlays appear in captured frames
- [ ] `html2canvas` CDN loads without errors
- [ ] No `restore_size` artifacts (message type and handlers removed)
- [ ] All 97 existing tests pass
- [ ] Browser console has no errors
- [ ] No new Python dependencies
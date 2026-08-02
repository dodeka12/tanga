# Phase 12 — Title & Annotation (Markdown + Math Formulas)

**Prerequisites:** Phase 8a (unified overlay system with `layer: "overlay"`,
`positioning: "fixed"`), Phase 4d (labels as first-class overlay objects)

**Goal:** Add a **title** overlay and a **markdown annotation area** to the 3D
viewer. The title is displayed as a fixed-position heading at the top of the
viewport. The annotation area renders markdown text (including LaTeX math
formulas like `$e^{i\pi} = -1$` and `$$\int_0^\infty$$`) as HTML in a
fixed-position panel below the 3D canvas. The markdown text is passed from
Python via the existing WebSocket pipeline — no build tools, no npm, just two
CDN libraries loaded in the browser.

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Use Cases

- Give a visualization a readable **title** (e.g., "PGA3 — Motor Interpolation")
  that stays visible even when the camera moves.
- Provide **explanatory text** describing what the visualization shows: geometric
  interpretations, algebraic derivations, or step-by-step descriptions of a
  construction.
- Include **math formulas** in the annotation using standard LaTeX syntax
  (`$...$` for inline, `$$...$$` for display-style).
- Annotations update live — change the text mid-animation to describe what is
  happening at each step.

### 1.2 Current State

- `Visualizer.__init__` already accepts a `title` parameter stored as
  `self._title`, but it is only used for the HTML `<title>` tag (browser tab).
  It is **not displayed in the viewport**.
- The overlay system (Phase 8a) has `layer: "overlay"` with
  `positioning: "fixed"` and `buildOverlayElement()` dispatching on `kind`.
  Currently only `"label"` is implemented.
- There is no mechanism to pass arbitrary markdown text to the frontend or
  render it as HTML.

### 1.3 Design Goals

1. **Title:** Display the `Visualizer.title` string as a fixed-position H1/H2
   overlay at the top of the viewport.  Always visible, does not move with the
   3D camera.

2. **Annotation:** Accept markdown text (plain string from Python), render it
   to HTML in the browser using the **marked** library, then render LaTeX math
   formulas using **KaTeX**.  The rendered content is displayed in a
   fixed-position, scrollable panel.

3. **Live updates:** The annotation can be changed at any time (e.g., during
   animation) and the panel updates immediately — no page reload.

4. **Zero frontend build step.**  Both `marked` and `KaTeX` are loaded as
   plain `<script>` / `<link>` tags from CDN — same pattern as the existing
   Three.js import map.

5. **Python-first API.**  Users set the title at construction time and pass
   markdown via a simple method call or constructor parameter:

   ```python
   viz = Visualizer(title="My Construction", annotation="## Step 1\n\n...")
   # or
   viz.set_annotation("## Step 2\n\n$e^{i\\pi} = -1$")
   ```

---

## 2. Technical Approach

### 2.1 Why Fixed-Position DOM (Not CSS2DRenderer in 3D Scene)

| Approach | Pros | Cons |
|----------|------|------|
| CSS2DRenderer in 3D space | Title follows the scene | Moves with camera, perspective distortion, hard to read |
| **Fixed-position DOM** (chosen) | Always readable, full HTML/CSS, scrollable | Uses screen real estate |

For a title and explanatory text that should remain readable regardless of
camera orientation, fixed-position DOM elements are the correct choice.
Phase 8a already defines `positioning: "fixed"` in the overlay system for
exactly this use case — the infrastructure is in place.

### 2.2 CDN Libraries

Both libraries are loaded as simple `<script>` / `<link>` tags — zero
dependencies, no module imports:

| Library | Version | CDN URL | Purpose |
|---------|---------|---------|---------|
| **marked** | ^15.0 | `https://unpkg.com/marked/marked.min.js` | Markdown → HTML (same CDN as Three.js) |
| **KaTeX** | ^0.16 | `https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.css` + `.js` | LaTeX math formula rendering |
| **KaTeX auto-render** | ^0.16 | `https://cdn.jsdelivr.net/npm/katex@0.16/dist/contrib/auto-render.min.js` | Auto-detects `$...$` and `$$...$$` in rendered HTML |

**Workflow in the browser:** `marked.parse(markdownText)` → HTML string →
`renderMathInElement(container)` → formulas rendered as KaTeX spans.

**Why `marked` over alternatives:** It's the most widely used, has zero
dependencies, is already on the same CDN provider (`unpkg.com`) used for
Three.js, and has a simple synchronous `marked.parse()` API.

**Why KaTeX over MathJax:** KaTeX is ~10× faster for initial render, has no
async load complexity, and handles the subset of LaTeX used in geometric
descriptions (fractions, exponents, Greek letters, integrals, matrices).

---

## 3. JSON Message Format

### 3.1 Title — Extended `scene_config`

The title is scene-level configuration, not an individual object. It is sent
once on WebSocket connect (and can be re-sent if the title changes):

```json
{
  "type": "scene_config",
  "space_extent": 10.0,
  "show_grid": true,
  "show_axes": true,
  "background_color": "#1a1a2e",
  "title": "My Visualization Title",
  "camera": { ... }
}
```

### 3.2 Annotation — Overlay Object

The annotation is sent as a unified overlay object (Phase 8a pattern).
It can be updated at any time via the regular scene update pipeline:

```json
{
  "type": "scene_update",
  "objects": [
    {
      "id": "annotation_1",
      "layer": "overlay",
      "kind": "annotation",
      "positioning": "fixed",
      "anchor": "bottom",
      "offset": [0, 0],
      "text": "# My Markdown\n\nThis is a paragraph with math: $e^{i\\pi} = -1$.\n\n---\n\n## Subheading\n\n$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$",
      "style": {
        "style_type": "AnnotationStyle",
        "width": "100%",
        "max_width": "800px",
        "max_height": "300px",
        "font_size": 13,
        "color": "#cccccc",
        "background": "rgba(0, 0, 0, 0.75)"
      }
    }
  ],
  "removed": []
}
```

Key design decisions:
- `kind: "annotation"` — new overlay kind, dispatched by `buildOverlayElement()`.
- `positioning: "fixed"` — stays at a fixed screen position, does not track 3D
  coordinates.
- `anchor: "bottom"` — the annotation panel is anchored to the bottom of the
  viewport. Other anchors (`"top"`, `"top-left"`, etc.) can be added later.
- `text` contains the raw markdown string. The frontend renders it to HTML +
  KaTeX formulas.
- `style` is an `AnnotationStyle` instance (see §4.3) controlling appearance.

### 3.3 Title as Overlay Object (Alternative)

If we want to update the title dynamically, it could also be an overlay object:

```json
{
  "id": "title_1",
  "layer": "overlay",
  "kind": "title",
  "positioning": "fixed",
  "anchor": "top",
  "offset": [0, 10],
  "text": "My Visualization Title",
  "style": {
    "style_type": "TitleStyle",
    "font_size": 20,
    "color": "#ffffff",
    "background": "transparent"
  }
}
```

**Decision:** The title is sent **both** ways:
1. Initially via `scene_config.title` (simple, one-time setup).
2. Optionally as an overlay object with `kind: "title"` if dynamic title
   updates are needed. Phase 12 implements the `scene_config` path; the
   overlay object path is a natural extension without additional plumbing.

---

## 4. Python Side

### 4.1 `Visualizer.__init__` Extensions

Add an `annotation` parameter:

```python
class Visualizer:
    def __init__(
        self,
        *,
        port: int = 8765,
        host: str = "localhost",
        open_browser: bool | None = None,
        opns: bool = True,
        title: str = "Tanga 3D Viewer",
        annotation: str | None = None,  # ← NEW
        # Scene configuration
        space_extent: float = 10.0,
        show_grid: bool = True,
        show_axes: bool = True,
        background_color: str = "#1a1a2e",
        # Camera configuration
        camera: CameraConfig | None = None,
    ) -> None:
        ...
        self._annotation = annotation  # stored for initial send
```

### 4.2 `SceneConfig` Extensions

Add `title` and `annotation` fields to the scene config dataclass:

```python
@dataclass
class SceneConfig:
    space_extent: float = 10.0
    show_grid: bool = True
    show_axes: bool = True
    background_color: str = "#1a1a2e"
    camera: CameraConfig | None = None
    title: str = "Tanga 3D Viewer"          # ← NEW
    annotation: str | None = None           # ← NEW

    def to_dict(self) -> dict:
        result = {
            "type": "scene_config",
            "space_extent": self.space_extent,
            "show_grid": self.show_grid,
            "show_axes": self.show_axes,
            "background_color": self.background_color,
            "title": self.title,            # ← NEW
        }
        if self.camera is not None:
            cam = self.camera.to_dict()
            if cam:
                result["camera"] = cam
        if self.annotation is not None:     # ← NEW
            result["annotation"] = self.annotation
        return result
```

### 4.3 `AnnotationStyle` Dataclass

A new style class in `_styles.py` for controlling the annotation panel
appearance:

```python
@dataclass
class AnnotationStyle(VizStyle):
    """Visual style for the markdown annotation panel."""

    width: str = "100%"
    max_width: str = "800px"
    max_height: str = "250px"
    font_size: float = 13
    font_family: str = "sans-serif"
    color: str = "#cccccc"
    background: str = "rgba(0, 0, 0, 0.75)"
    link_color: str = "#88ccff"
    code_background: str = "rgba(255, 255, 255, 0.1)"
    padding: str = "10px 16px"
    border_radius: str = "4px"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "AnnotationStyle"}
        for fld in fields(self):
            val = getattr(self, fld.name)
            if val is not None:
                result[fld.name] = val
        return result
```

### 4.4 `Visualizer.set_annotation()` Method

For live updates during animation:

```python
def set_annotation(self, text: str | None) -> None:
    """Set or update the markdown annotation text.

    Pass ``None`` to hide the annotation panel.  The text is rendered
    as Markdown with LaTeX math (``$...$`` inline, ``$$...$$`` display)
    in the browser.

    Example::

        viz.set_annotation("## Step 2\\\\n\\\\n$R = e^{-i\\\\theta/2}$")
    """
    from ._scene_objects import SceneObject

    self._annotation = text

    if text is None:
        self._scene.remove_object("__annotation__")
    else:
        obj = SceneObject(
            id="__annotation__",
            layer="overlay",
            kind="annotation",
            data={"text": text, "style": self._annotation_style.to_dict()},
        )
        self._scene.add_object(obj)

    # Force a flush so the update reaches the browser immediately
    self.flush()
```

### 4.5 `Visualizer.set_title()` Method

```python
def set_title(self, title: str) -> None:
    """Update the viewport title.

    Changes the title displayed at the top of the 3D viewport
    (in addition to the browser tab title).
    """
    self._title = title
    self._config.title = title

    # If server is running, push updated scene_config
    if self._server is not None:
        self._push_scene_config()
```

### 4.6 Auto-Send on Connect

When a new WebSocket client connects, the server already sends `scene_config`
(Phase 3/4). After this phase, that message includes `title` and optionally
`annotation`. The JS side caches and renders both.

---

## 5. Frontend Side

### 5.1 `viewer.html` — CDN Dependencies

Add three new tags in the `<head>`:

```html
<!-- Markdown rendering -->
<script src="https://unpkg.com/marked/marked.min.js"></script>

<!-- KaTeX for math formulas -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
```

**Design note:** `marked` and `KaTeX` are loaded as classic `<script>` tags
(not ES modules). This is intentional — they are not part of the module
dependency graph and are available as global variables (`marked`, `katex`,
`renderMathInElement`).  The same approach is used by the Three.js CDN
community for non-module libraries.

### 5.2 `viewer.js` — Apply Scene Config with Title

Extend `applySceneConfig()` to cache and render the title:

```javascript
let annotationPanel = null;

function applySceneConfig(config) {
    sceneConfig = config;

    // ... existing background, grid, axes, camera code ...

    // ── Title ──
    if (config.title !== undefined) {
        renderTitle(config.title);
    }

    // ── Annotation ──
    if (config.annotation !== undefined) {
        renderAnnotation(config.annotation);
    } else {
        removeAnnotation();
    }
}

let titleElement = null;

function renderTitle(titleText) {
    if (!titleElement) {
        titleElement = document.createElement('div');
        titleElement.style.position = 'fixed';
        titleElement.style.top = '10px';
        titleElement.style.left = '50%';
        titleElement.style.transform = 'translateX(-50%)';
        titleElement.style.color = '#ffffff';
        titleElement.style.fontFamily = 'sans-serif';
        titleElement.style.fontSize = '20px';
        titleElement.style.fontWeight = 'bold';
        titleElement.style.background = 'rgba(0, 0, 0, 0.6)';
        titleElement.style.padding = '6px 20px';
        titleElement.style.borderRadius = '4px';
        titleElement.style.pointerEvents = 'none';
        titleElement.style.zIndex = '5';
        document.body.appendChild(titleElement);
    }
    titleElement.textContent = titleText;
}
```

### 5.3 `viewer.js` — `buildOverlayElement()` for Annotations

Add a new `case 'annotation'` to the existing `buildOverlayElement()`
function (which already dispatches on `msg.kind` for labels):

```javascript
function buildOverlayElement(msg) {
    switch (msg.kind) {
        case 'label': {
            // ... existing label code ...
        }

        case 'annotation': {
            if (!msg.text) return null;

            const container = document.createElement('div');

            // Render markdown to HTML
            if (typeof marked !== 'undefined') {
                container.innerHTML = marked.parse(msg.text);
            } else {
                // Fallback: plain text if marked is not loaded
                container.textContent = msg.text;
            }

            // Render KaTeX formulas
            if (typeof renderMathInElement !== 'undefined') {
                try {
                    renderMathInElement(container, {
                        delimiters: [
                            {left: '$$', right: '$$', display: true},
                            {left: '$', right: '$', display: false},
                        ],
                        throwOnError: false,
                    });
                } catch (e) {
                    console.warn('KaTeX rendering error:', e);
                }
            }

            // Base styling
            const s = msg.style || {};
            container.style.position = 'fixed';
            container.style.bottom = (msg.offset || [0, 0])[1] + 'px';
            container.style.left = '50%';
            container.style.transform = 'translateX(-50%)';
            container.style.width = s.width || '100%';
            container.style.maxWidth = s.max_width || '800px';
            container.style.maxHeight = s.max_height || '250px';
            container.style.overflowY = 'auto';
            container.style.fontFamily = s.font_family || 'sans-serif';
            container.style.fontSize = (s.font_size || 13) + 'px';
            container.style.color = s.color || '#cccccc';
            container.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.75)';
            container.style.padding = s.padding || '10px 16px';
            container.style.borderRadius = s.border_radius || '4px';
            container.style.zIndex = '5';
            container.style.lineHeight = '1.5';

            // Inline styles for rendered content
            const styleEl = document.createElement('style');
            styleEl.textContent = `
                .annotation-container h1, .annotation-container h2, .annotation-container h3,
                .annotation-container h4, .annotation-container h5, .annotation-container h6 {
                    margin-top: 0.6em; margin-bottom: 0.3em;
                }
                .annotation-container h1 { font-size: 1.3em; }
                .annotation-container h2 { font-size: 1.15em; }
                .annotation-container h3 { font-size: 1.05em; }
                .annotation-container p { margin: 0.3em 0; }
                .annotation-container a { color: ${s.link_color || '#88ccff'}; }
                .annotation-container code {
                    background: ${s.code_background || 'rgba(255,255,255,0.1)'};
                    padding: 1px 4px; border-radius: 3px;
                }
                .annotation-container pre {
                    background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px;
                    overflow-x: auto;
                }
                .annotation-container hr { border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 0.5em 0; }
                .annotation-container .katex { font-size: 1.05em; }
            `;
            container.appendChild(styleEl);
            // Wrap content in a div for scoped styling
            const content = container.querySelector('div') || container;
            content.className = 'annotation-container';

            // Store reference for later removal
            annotationPanel = container;
            return container;
        }

        case 'title': {
            // Dynamic title overlay (future extension)
            if (!msg.text) return null;
            const div = document.createElement('div');
            div.textContent = msg.text;
            div.style.position = 'fixed';
            div.style.top = '10px';
            div.style.left = '50%';
            div.style.transform = 'translateX(-50%)';
            div.style.color = '#ffffff';
            div.style.fontFamily = 'sans-serif';
            div.style.fontSize = (msg.style?.font_size || 20) + 'px';
            div.style.fontWeight = 'bold';
            div.style.background = 'rgba(0, 0, 0, 0.6)';
            div.style.padding = '6px 20px';
            div.style.borderRadius = '4px';
            div.style.pointerEvents = 'none';
            div.style.zIndex = '5';
            return div;
        }

        default:
            console.warn('Unknown overlay kind: ' + msg.kind);
            return null;
    }
}
```

### 5.4 Render Loop — No Changes Needed

The annotation and title are fixed-position DOM elements. They are rendered
by the browser's layout engine, not by the Three.js render loop.  CSS2DRenderer
continues to handle only 3D-tracked labels.

### 5.5 Removal on `scene_update`

When `scene_update` contains `"removed": ["__annotation__"]`, the existing
`upsertObject()` logic removes the DOM element automatically. The
`annotationPanel` reference is also cleared.

---

## 6. Files to Create / Modify

### 6.1 New Files

| File | Content |
|------|---------|
| `py/tests/viz/test_phase12_title_annotation.py` | Tests for `SceneConfig.title`/`.annotation`, `AnnotationStyle`, markdown JSON output |

### 6.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/_styles.py` | Add `AnnotationStyle` dataclass (empty fields, canonical defaults in `_DEFAULT_STYLE_FOR_KIND`) and `TitleStyle` dataclass |
| `py/pytanga/viz/scene.py` | Add `title` and `annotation` fields to `SceneConfig`; include in `to_dict()` |
| `py/pytanga/viz/visualizer.py` | Add `annotation` parameter to `__init__`; add `set_annotation()` and `set_title()` methods; pass `title`/`annotation` to `SceneConfig` |
| `py/pytanga/viz/server.py` | No changes — `scene_config` is already pushed on connect; the extended dict just carries more fields |
| `py/pytanga/viz/serializer.py` | No changes — the annotation is sent as an overlay object, not a serialized entity |
| `py/pytanga/viz/templates/viewer.html` | Add `<script>` tags for `marked` and KaTeX CSS/JS |
| `py/pytanga/viz/templates/viewer.js` | Extend `applySceneConfig()` for title; add `case 'annotation'` and `case 'title'` to `buildOverlayElement()` |
| `py/pytanga/viz/export/_html.py` | Extend bootstrap adapter: include `marked`/KaTeX CDN links; render title and annotation from embedded scene data |
| `py/pytanga/viz/__init__.py` | Export `AnnotationStyle`, `TitleStyle` (if needed by users) |

### 6.3 Files NOT Modified

- `py/pytanga/viz/_props.py` — unchanged (color normalization utility)
- `py/pytanga/viz/_label.py` — unchanged (label logic)
- `py/pytanga/viz/_label_frame.py` — unchanged
- `py/pytanga/viz/_types.py` — unchanged
- Per-entity JS renderers — unchanged
- Operator JS renderers — unchanged
- `py/pytanga/viz/templates/controls.js` — unchanged
- `py/pytanga/viz/templates/animator.js` — unchanged

---

## 7. Implementation Checklist

### 7.1 `_styles.py` — New Style Classes

- [ ] **S1:** Add `AnnotationStyle(VizStyle)` dataclass with `width`, `max_width`, `max_height`, `font_size`, `font_family`, `color`, `background`, `link_color`, `code_background`, `padding`, `border_radius`
- [ ] **S2:** All fields default to `None` (canonical values in a module-level `_DEFAULT_ANNOTATION_STYLE`)
- [ ] **S3:** Implement `AnnotationStyle.to_dict()` — include `style_type: "AnnotationStyle"`, omit `None` values
- [ ] **S4:** Add `TitleStyle(VizStyle)` dataclass with `font_size`, `color`, `background` (all `None` defaults)
- [ ] **S5:** Implement `TitleStyle.to_dict()`

### 7.2 `scene.py` — SceneConfig Extensions

- [ ] **C1:** Add `title: str = "Tanga 3D Viewer"` field to `SceneConfig`
- [ ] **C2:** Add `annotation: str | None = None` field to `SceneConfig`
- [ ] **C3:** Include `"title"` in `SceneConfig.to_dict()` output
- [ ] **C4:** Include `"annotation"` in `SceneConfig.to_dict()` output (only when non-`None`)

### 7.3 `visualizer.py` — API Extensions

- [ ] **V1:** Add `annotation: str | None = None` parameter to `Visualizer.__init__`
- [ ] **V2:** Store `self._annotation = annotation` and `self._annotation_style` (canonical `AnnotationStyle` instance)
- [ ] **V3:** Pass `title` and `annotation` to `SceneConfig` constructor
- [ ] **V4:** Implement `set_annotation(text: str | None)` method:
  - Stores `self._annotation = text`
  - Creates/removes a `SceneObject` with `id="__annotation__"`, `kind="annotation"`, `layer="overlay"`
  - Calls `self.flush()` to push immediately
- [ ] **V5:** Implement `set_title(title: str)` method:
  - Updates `self._title` and `self._config.title`
  - Pushes updated `scene_config` to connected clients (if server is running)
- [ ] **V6:** Implement `_push_scene_config()` helper for re-sending config on title change

### 7.4 `viewer.html` — CDN Dependencies

- [ ] **H1:** Add `<script src="https://unpkg.com/marked/marked.min.js">` in `<head>`
- [ ] **H2:** Add KaTeX CSS: `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">`
- [ ] **H3:** Add KaTeX JS: `<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js">`
- [ ] **H4:** Add KaTeX auto-render: `<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js">`

### 7.5 `viewer.js` — Title & Annotation Rendering

- [ ] **J1:** Extend `applySceneConfig()` to call `renderTitle(config.title)` when `config.title` is present
- [ ] **J2:** Implement `renderTitle(titleText)` — creates/updates a fixed-position title div at top-center of viewport
- [ ] **J3:** Add `case 'annotation'` to `buildOverlayElement()`:
  - Render markdown via `marked.parse(msg.text)` (with fallback to plain text)
  - Render KaTeX via `renderMathInElement(container, {delimiters: [...], throwOnError: false})`
  - Style the container as a fixed-position bottom panel
  - Inject scoped CSS for headings, code, links, KaTeX elements
- [ ] **J4:** Add `case 'title'` to `buildOverlayElement()` for dynamic title overlay objects
- [ ] **J5:** Call `removeAnnotation()` when `scene_config.annotation` is `None` or `""`
- [ ] **J6:** Ensure annotation panel is removed when `"removed"` includes `"__annotation__"` (handled by existing `upsertObject` logic)
- [ ] **J7:** Handle empty annotation text gracefully (hide panel, don't render empty div)

### 7.6 Export HTML (`_html.py`)

- [ ] **E1:** Add `<script>` and `<link>` tags for `marked` and KaTeX in the export HTML template
- [ ] **E2:** Include `title` in the embedded `#tanga-scene-config` JSON
- [ ] **E3:** Include `annotation` in the embedded `#tanga-scene-config` JSON (if present)
- [ ] **E4:** Bootstrap script renders title and annotation on load (mirrors `applySceneConfig` and `buildOverlayElement` logic)
- [ ] **E5:** Annotation panel has the same fixed-position styling as the live viewer

### 7.7 `__init__.py`

- [ ] **I1:** Export `AnnotationStyle` and `TitleStyle` (if intended for public use)

### 7.8 Tests

- [ ] **T1:** Test `AnnotationStyle().to_dict()` returns `{"style_type": "AnnotationStyle"}`
- [ ] **T2:** Test `AnnotationStyle(font_size=16, color="#fff").to_dict()` includes only non-None fields
- [ ] **T3:** Test `SceneConfig(title="My Viz").to_dict()` includes `"title": "My Viz"`
- [ ] **T4:** Test `SceneConfig(annotation="# Hello").to_dict()` includes `"annotation": "# Hello"`
- [ ] **T5:** Test `SceneConfig().to_dict()` omits `"annotation"` when `None`
- [ ] **T6:** Test `Visualizer(title="Test", annotation="# md")` stores both values
- [ ] **T7:** Test `viz.set_annotation("new markdown")` creates a `SceneObject` with correct fields
- [ ] **T8:** Test `viz.set_annotation(None)` removes the annotation `SceneObject`
- [ ] **T9:** Test `viz.set_title("New Title")` updates `self._config.title`
- [ ] **T10:** All existing tests pass (no regressions)

### 7.9 Smoke / Manual Verification

- [ ] **M1:** `Visualizer(title="My Title").run()` — title displayed at top of viewport, `<title>` tag updated
- [ ] **M2:** `Visualizer(annotation="# Hello\n\n$e=mc^2$").run()` — annotation panel with rendered markdown and KaTeX formula
- [ ] **M3:** `viz.set_annotation("## Step 2\n\n$$\\nabla^2\\phi = 0$$")` — annotation updates live
- [ ] **M4:** `viz.set_annotation(None)` — annotation panel disappears
- [ ] **M5:** `viz.set_title("Updated Title")` — title changes in viewport
- [ ] **M6:** Title and annotation do not interfere with orbit controls
- [ ] **M7:** Annotation panel is scrollable when content exceeds `max_height`
- [ ] **M8:** `viz.export_html("scene.html")` — exported file renders title and annotation correctly
- [ ] **M9:** Browser console has no errors (no missing CDN resources)
- [ ] **M10:** KaTeX formulas render correctly: inline `$x^2$`, display `$$\int$$`, Greek letters, fractions, matrices
- [ ] **M11:** Markdown features work: headings, bold, italic, code blocks, links, horizontal rules

---

## 8. Verification Checklist

- [ ] `SceneConfig` carries `title` and `annotation` fields
- [ ] `scene_config` WebSocket message includes title and annotation
- [ ] Title displayed as fixed-position overlay at top of viewport
- [ ] Annotation panel renders markdown → HTML via `marked`
- [ ] Annotation panel renders LaTeX formulas via KaTeX (`$...$` and `$$...$$`)
- [ ] `set_annotation()` updates the annotation live
- [ ] `set_annotation(None)` hides the panel
- [ ] `set_title()` updates the title live
- [ ] Exported HTML self-contained file includes title + annotation rendering
- [ ] No CDN load errors in browser console
- [ ] No interference with orbit controls or 3D scene interaction
- [ ] All existing tests pass
- [ ] No circular imports introduced

---

## 9. Usage Examples

### 9.1 Basic Title and Annotation

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere

viz = Visualizer(
    title="PGA3 — Sphere Visualization",
    annotation="""## Sphere at Origin

A sphere of radius $r = 2.5$ centered at the origin.

The equation in PGA3 is: $p \\cdot p = r^2$

In conformal GA (N3), a sphere is represented as a grade-1 vector:
$$S = o - \\frac{1}{2} r^2 \\infty$$

where $o$ is the origin point and $\\infty$ is the point at infinity.
""",
)

viz.add(Point(1, 2, 3), color="#ff4444", size=0.12, label="P₁")
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)
viz.run()
```

### 9.2 Live Annotation Updates During Animation

```python
import time, math
from pytanga.viz import Visualizer
from pytanga.geometry import Point

viz = Visualizer(title="Rotating Point")

viz.start()
point_id = viz.add(Point(3, 0, 0), color="#ff4444", size=0.12)
viz.flush()

# Update annotation as the animation progresses
angles = [0, 45, 90, 135, 180, 225, 270, 315, 360]
for angle_deg in angles:
    angle_rad = math.radians(angle_deg)
    x = 3 * math.cos(angle_rad)
    y = 3 * math.sin(angle_rad)

    viz.update_entity(point_id, Point(x, y, 0))
    viz.set_annotation(f"## Angle: {angle_deg}°\n\n"
                       f"Position: $({x:.2f}, {y:.2f}, 0)$\n\n"
                       f"Rotation: $R = e^{{-i\\\\theta/2}}, "
                       f"\\\\theta = {angle_rad:.3f}$ rad")
    viz.flush()
    time.sleep(0.5)

viz.set_annotation(None)  # Hide annotation
viz.flush()
time.sleep(2)
viz.stop()
```

---

## 10. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **8a** | Phase 12 builds on the unified overlay system (`layer: "overlay"`, `positioning: "fixed"`, `buildOverlayElement()` dispatch). Must be implemented after 8a. |
| **4d** | Labels (Phase 4d) and annotations share the overlay dispatch pattern but are separate `kind` values. No conflict. |
| **8c** | Label offset/alignment changes in 8c do not affect annotations (annotations use fixed positioning, not 3D-anchored). |
| **11** | Export HTML adapter must include `marked`/KaTeX CDN links and render logic. The annotation text is embedded in the exported HTML, so it works offline (after CDN load). |
| **10** | Example demos should showcase title + annotation with math formulas. |
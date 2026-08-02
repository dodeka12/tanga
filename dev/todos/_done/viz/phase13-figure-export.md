# Phase 13 — Figure Export for HTML Presentations

**Prerequisites:** Phase 12 (title, annotation, markdown, KaTeX), Phase 11 (HTML export)

**Goal:** Add a dedicated **presentation figure export** — an HTML snippet export
mode that produces a self-contained `<div>` + `<script>` block suitable for direct
inclusion in reveal.js, Slidev, Marp, or any HTML-based presentation framework.
Supports configurable dimensions, transparent background, auto-rotation, and
optional title/footer overlays.  Export can optionally launch a stand-alone
browser window sized to the exact figure dimensions so it looks like a desktop
app screenshot.

A `FigureStyle` dataclass controls visual presentation options.

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Use Cases

- Embed an interactive 3D figure in a **reveal.js** presentation slide alongside
  explanatory markdown text.
- Publish a supplementary figure for a paper where readers can rotate and explore
  a geometric construction directly in the browser.
- Export a "screenshot-sized" interactive figure that can be embedded in a blog
  post, documentation page, or JupyterBook.
- Demo a construction in a stand-alone browser window with no browser chrome
  — just the 3D figure, title, and optional annotation / footer.

### 1.2 Current State

- `viz.export_html()` (Phase 11) produces a **full-page** HTML document:
  - `html,body { width:100%; height:100%; overflow:hidden; background:#1a1a2e }`
  - The Three.js canvas fills the entire viewport.
  - It cannot be embedded in a slide without an `<iframe>`.
- `viz.export_glb()` (Phase 11) works with `<model-viewer>` which is great for
  simple meshes, but does not support CSS2D labels, annotations, or KaTeX math.

### 1.3 What a Figure Export Adds

| Feature | HTML Export (Phase 11) | Figure Export (Phase 13) |
|---------|------------------------|--------------------------|
| Embeddable in presentations | ❌ (needs iframe) | ✅ (self-contained `<div>` + `<script>`) |
| Fixed dimensions | ❌ (full viewport) | ✅ (configurable `width × height`) |
| Transparent background | ❌ | ✅ (`background: transparent`) |
| Auto-rotate (passive display) | ❌ | ✅ (`auto_rotate: true`) |
| Kanban-style footer | ❌ | ✅ (markdown text below the 3D canvas) |
| Title overlay | ✅ | ✅ (optional) |
| Markdown annotation | ✅ (full-width bottom panel) | ✅ (optional, same styling) |
| Stand-alone browser window | ❌ | ✅ (opens at exact figure dimensions) |
| OrbitControls (rotate/pan/zoom) | ✅ | ✅ |
| Labels with KaTeX math | ✅ | ✅ |

### 1.4 Design Goals

1. **Snippet-based output** — the export is a `<div>` + `<script type="module">`
   block that can be pasted directly into a presentation slide's HTML.  No
   `<html>`, no `<head>`, no global style resets.

2. **CSS isolation** — all styles are scoped to the figure container via a
   unique ID.  No `* { margin: 0 }` style resets that would break the
   parent page.

3. **`FigureStyle`** — a new `VizStyle` subclass controlling:
   `width`, `height`, `background`, `auto_rotate`, `show_title`,
   `show_annotation`, `show_grid`, `show_axes`, `border_radius`.

4. **`FigureConfig`** — a new dataclass collecting all figure-level parameters
   (`title`, `target`, `annotation`, `footer`, `background`, `browser_width`,
   `browser_height`).  `target` is a CSS selector string (default `"body"`)
   for the DOM mount point; in a standalone export it generates a minimal
   wrapper page.

5. **`Visualizer.__init__` integration** — the existing `title` and `annotation`
   kwargs continue to work as convenience shortcuts but are stored in a
   `FigureConfig` instance internally.  Users can pass `figure_config=FigureConfig(...)`
   to set all figure parameters at once, or mutate `viz.figure_config` for
   auto-complete access.

6. **`scene_config` carries FigureConfig** — the `scene_config` WebSocket
   message already includes `title` and `annotation`.  Phase 13 adds
   `figure` sub-object with `width`, `height`, `background`, `auto_rotate`,
   `show_title`, `show_annotation` so the live viewer can also render in
   "figure mode".

7. **Standalone browser launch** — `viz.open_figure(browser_width, browser_height)`
   opens a browser window sized to the exact figure dimensions, positioned
   (on multi-monitor setups) to a configurable screen.

8. **Backward compatible** — `viz.export_html()`, `viz.export_glb()`, and
   `viz.run()` are unchanged.  The live viewer continues to work as a
   full-viewport application.

---

## 2. `FigureStyle` Dataclass

```python
# py/pytanga/viz/_styles.py

@dataclass
class FigureStyle(VizStyle):
    """Visual style for figure exports and live "figure mode".

    Controls the appearance of the 3D canvas container — dimensions,
    background, auto-rotation, and which overlays to show.
    """

    width: int | None = None          # px (default 800)
    height: int | None = None         # px (default 600)
    background: str | None = None     # CSS background (default "transparent")
    auto_rotate: bool | None = None   # auto-rotate the camera (default False)
    show_grid: bool | None = None     # show grid (default True)
    show_axes: bool | None = None     # show axes (default True)
    show_title: bool | None = None    # show title overlay (default True)
    show_annotation: bool | None = None  # show annotation panel (default True)
    border_radius: str | None = None  # CSS border-radius (default "0")

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "FigureStyle"}
        if self.width is not None:
            result["width"] = self.width
        if self.height is not None:
            result["height"] = self.height
        if self.background is not None:
            result["background"] = self.background
        if self.auto_rotate is not None:
            result["auto_rotate"] = self.auto_rotate
        if self.show_grid is not None:
            result["show_grid"] = self.show_grid
        if self.show_axes is not None:
            result["show_axes"] = self.show_axes
        if self.show_title is not None:
            result["show_title"] = self.show_title
        if self.show_annotation is not None:
            result["show_annotation"] = self.show_annotation
        if self.border_radius is not None:
            result["border_radius"] = self.border_radius
        return result
```

### 2.1 Canonical Default

```python
# In Visualizer.__init__:
from ._styles import FigureStyle as _FS

self._default_figure_style = _FS(
    width=800,
    height=600,
    background="transparent",
    auto_rotate=False,
    show_grid=True,
    show_axes=True,
    show_title=True,
    show_annotation=True,
    border_radius="0",
)
```

---

## 3. `FigureConfig` Dataclass

```python
# py/pytanga/viz/scene.py — or a new _figure.py

@dataclass
class FigureConfig:
    """Figure-level parameters for exports and live figure mode.

    Separate from ``FigureStyle`` — this holds content and layout
    parameters, while ``FigureStyle`` holds visual presentation.
    """

    title: str = "Tanga 3D Viewer"
    target: str = "body"               # CSS selector for DOM mount point
    annotation: str | None = None      # markdown text for annotation panel
    footer: str | None = None          # markdown text for footer area
    background: str = "#1a1a2e"        # CSS background for the figure container
    browser_width: int | None = None   # standalone browser window width (px)
    browser_height: int | None = None  # standalone browser window height (px)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "title": self.title,
            "target": self.target,
            "background": self.background,
        }
        if self.annotation is not None:
            result["annotation"] = self.annotation
        if self.footer is not None:
            result["footer"] = self.footer
        if self.browser_width is not None:
            result["browser_width"] = self.browser_width
        if self.browser_height is not None:
            result["browser_height"] = self.browser_height
        return result
```

### 3.1 Integration with `Visualizer`

```python
class Visualizer:
    def __init__(
        self,
        *,
        # ... existing params ...
        title: str = "Tanga 3D Viewer",
        annotation: str | None = None,
        figure_config: FigureConfig | None = None,
        # ... scene/camera params ...
    ) -> None:
        # Build FigureConfig from explicit kwargs or combined object
        if figure_config is not None:
            self._figure_config = figure_config
            # title/annotation kwargs override FigureConfig fields
            if title != "Tanga 3D Viewer":
                self._figure_config.title = title
            if annotation is not None:
                self._figure_config.annotation = annotation
        else:
            self._figure_config = FigureConfig(
                title=title,
                annotation=annotation,
            )

        # SceneConfig still carries the effective title/annotation for
        # the live viewer's scene_config message:
        self._config = SceneConfig(
            title=self._figure_config.title,
            annotation=self._figure_config.annotation,
            ...
        )

    @property
    def figure_config(self) -> FigureConfig:
        """The current ``FigureConfig`` — mutate for auto-complete.

        Example::

            viz.figure_config.footer = "## Legend\\\\n\\\\nRed = Sphere A"
            viz.figure_config.target = "#my-slide-div"
        """
        return self._figure_config

    @property
    def default_figure_style(self) -> FigureStyle:
        """The canonical ``FigureStyle`` — mutate to change defaults.

        Example::

            viz.default_figure_style.width = 1024
            viz.default_figure_style.auto_rotate = True
        """
        return self._default_figure_style
```

### 3.2 `scene_config` Extension

`SceneConfig.to_dict()` already includes `title` and `annotation`.  Phase 13
adds a `"figure"` sub-object carrying FigureStyle parameters:

```json
{
  "type": "scene_config",
  "title": "My Figure",
  "annotation": "## Description",
  "figure": {
    "width": 800,
    "height": 600,
    "background": "transparent",
    "auto_rotate": false,
    "show_grid": true,
    "show_axes": true,
    "show_title": true,
    "show_annotation": true,
    "border_radius": "0"
  },
  "space_extent": 10,
  "background_color": "#1a1a2e",
  ...
}
```

The live viewer's `applySceneConfig()` checks `config.figure` and, if present,
adjusts the renderer size, background, and auto-rotate accordingly.  When
`config.figure` is absent the viewer renders in full-viewport mode as before.

---

## 4. Figure Export HTML Snippet

### 4.1 Export Format

The export is an **HTML snippet** (not a full document):

```html
<!-- Tanga 3D Figure — paste into any HTML page -->
<div id="tanga-figure-abc123"
     style="width:800px;height:600px;position:relative;overflow:hidden;
            background:transparent;border-radius:4px;">
</div>
<script type="module">
// ── Figure bootstrap ──
// (inlines the renderer modules, then mounts to #tanga-figure-abc123)
// ...
</script>
```

### 4.2 Bootstrap Logic (vs. Current Phase 11)

| Aspect | Phase 11 (HTML Export) | Phase 13 (Figure Export) |
|--------|----------------------|--------------------------|
| Container | `document.body` (full viewport) | `#tanga-figure-xxx` (fixed dimensions) |
| Renderer size | `window.innerWidth/Height` | Configurable `width × height` |
| Resize handler | Listens to `window.resize` | None (container is fixed) |
| Background | Solid dark (`#1a1a2e`) | Configurable (`transparent` for presentations) |
| OrbitControls `autoRotate` | `false` | Configurable (`false` for interactive, `true` for passive) |
| Title overlay | Always shown | Togglable via `FigureStyle.show_title` |
| Annotation panel | Always shown | Togglable via `FigureStyle.show_annotation` |
| Grid / axes | From `scene_config` | From `FigureStyle` (overrides `scene_config` if set) |
| Global style reset | `* { margin:0 }` | None — scoped to the figure div only |
| Footer | Not supported | Rendered from `figure_config.footer` as markdown below the canvas |
| Stand-alone browser window | Not supported | `viz.open_figure()` opens a minimal wrapper page at the configured dimensions |

### 4.3 CSS Isolation

All CSS is applied to the figure container div via inline `style` attributes.
No global selectors (`*`, `html`, `body`) are used.  The only exception is
the KaTeX stylesheet which is a `<link>` tag — this is acceptable since
KaTeX uses class-based selectors (`.katex`, `.katex-display`) which are
unlikely to conflict with presentation frameworks.

### 4.4 Snippet Structure

```html
<!-- Optional: KaTeX stylesheet (only needed for math in annotation/labels) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">

<div id="tanga-fig-{uuid}" style="width:{W}px;height:{H}px;position:relative;
  overflow:hidden;background:{BG};border-radius:{BR};">
  <!-- Title overlay (if show_title) -->
  <!-- Canvas (Three.js renderer) -->
  <!-- Annotation panel (if show_annotation) -->
  <!-- Footer (if footer text provided) -->
</div>

<!-- Inline script (exports do NOT rely on external .js files) -->
<script type="module">
  // ... Three.js CDN import map, renderer modules, figure bootstrap ...
</script>
```

### 4.5 Two Export Modes

| Method | Output | Use Case |
|--------|--------|----------|
| `viz.export_figure(path)` | HTML snippet file | Save to disk, include via `<include>` or copy-paste |
| `viz.export_figure_html()` | Returns the snippet as a Python `str` | Programmatic use, write to a file, or embed in a notebook |
| `viz.open_figure()` | Opens a browser window at figure dimensions | Quick preview of how the figure looks |

---

## 5. Python API

### 5.1 `Visualizer.export_figure()`

```python
def export_figure(
    self,
    path: str | Path,
    *,
    style: FigureStyle | None = None,
    overwrite: bool = False,
) -> None:
    """Export the current scene as an HTML snippet suitable for
    embedding in a presentation slide.

    The resulting file contains a ``<div>`` + ``<script type="module">``
    block — no ``<html>``, no ``<head>``, no global styles.

    Paste it directly into a reveal.js, Slidev, or Marp slide.

    Args:
        path: Output file path (e.g. ``"figure.html"``).
        style: Optional ``FigureStyle`` instance.  Only fields you
            set override the canonical defaults.
        overwrite: If ``False``, raise on existing file.
    """
```

### 5.2 `Visualizer.open_figure()`

```python
def open_figure(
    self,
    *,
    style: FigureStyle | None = None,
) -> None:
    """Open a standalone browser window sized to the figure dimensions.

    The window shows only the 3D figure — no browser chrome (toolbar,
    address bar, bookmarks).  Close the window or press Ctrl+C in the
    terminal to exit.

    Args:
        style: Optional ``FigureStyle`` instance.
    """
```

### 5.3 Usage Example

```python
from pytanga.viz import Visualizer, FigureStyle
from pytanga.geometry import Sphere, Point

viz = Visualizer(
    title="Sphere Construction",
    annotation="## Step 1\n\n$S = o - \\frac{1}{2} r^2 \\infty$",
)

viz.add(Sphere(Point(0, 0, 0), 2.5), wireframe=True, opacity=0.4)
viz.add(Point(0, 0, 0), color="#ff0", size=0.15, label="$O$")

viz.figure_config.footer = "**Figure 1:** A sphere of radius $r = 2.5$ centered at $O$."

# Export for presentations — transparent background, auto-rotate, rounded corners
viz.export_figure(
    "sphere_figure.html",
    style=FigureStyle(
        width=800,
        height=600,
        background="transparent",
        auto_rotate=True,
        border_radius="8px",
    ),
)

# Or preview in a standalone window
viz.open_figure(style=FigureStyle(width=800, height=600, auto_rotate=True))
```

---

## 6. Footer Rendering

The **footer** is a new concept introduced in Phase 13.  It is a short
markdown text block rendered **below** the 3D canvas, staying within the
figure `width × height` container.  Typical uses:

- Figure captions (e.g. "**Figure 1:** A geometric construction showing ...")
- Short legends / color keys
- Attribution or source notes

The footer is rendered via `marked.parse()` + `renderMathInElement()`,
same pipeline as the annotation panel.  It is part of `FigureConfig`
(not `FigureStyle`) because it carries content, not visual presentation.

```python
viz.figure_config.footer = "## Legend\n\nRed: Sphere A  |  Blue: Sphere B"
```

### 6.1 Layout

```
┌─────────────────────────────────────────┐
│  Title (if show_title)                  │ ← fixed overlay, top
├─────────────────────────────────────────┤
│                                         │
│         3D Canvas (Three.js)            │ ← fills remaining space
│                                         │
├─────────────────────────────────────────┤
│  Annotation (if show_annotation)        │ ← fixed overlay, bottom of canvas
├─────────────────────────────────────────┤
│  Footer (if footer text)                │ ← markdown area below canvas
└─────────────────────────────────────────┘
```

The footer lies **outside** the 3D canvas — it is a plain DOM element below
the renderer in the figure container's flex layout.  This means the footer
does NOT increase the canvas height; it pushes the total container height
beyond `style.height` if the user provides a fixed height, or is included
in the container's natural height if `style.height` is `"auto"`.

---

## 7. Files to Create / Modify

### 7.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/_figure.py` | `FigureConfig` dataclass + `to_dict()` |
| `py/pytanga/viz/export/_figure_html.py` | `render_export_figure()` — generates HTML snippet |
| `py/pytanga/viz/export/templates/figure_viewer.html` | Minimal wrapper page for `open_figure()` |
| `py/tests/viz/test_phase13_figure.py` | Tests for `FigureConfig`, `FigureStyle`, figure export |

### 7.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/_styles.py` | Add `FigureStyle` dataclass with `to_dict()` |
| `py/pytanga/viz/scene.py` | Add `"figure"` sub-object to `SceneConfig.to_dict()` |
| `py/pytanga/viz/visualizer.py` | Add `FigureConfig` storage, `figure_config` property, `default_figure_style` property, `export_figure()`, `open_figure()` methods |
| `py/pytanga/viz/__init__.py` | Export `FigureConfig`, `FigureStyle` |
| `py/pytanga/viz/templates/viewer.js` | In `applySceneConfig()`: if `config.figure` present, switch to figure mode (fixed dimensions, configurable auto-rotate, show/hide overlays, transparent background) |
| `py/pytanga/viz/templates/viewer.html` | No changes (live viewer in full-viewport mode is unchanged) |

### 7.3 Files NOT Modified

- `py/pytanga/viz/export/_html.py` — unchanged (full-page export)
- `py/pytanga/viz/export/_gltf.py` — unchanged
- `py/pytanga/viz/scene.py` `Scene` / `SceneObject` — unchanged
- `py/pytanga/viz/serializer.py` — unchanged
- `py/pytanga/viz/server.py` — unchanged
- Per-entity JS renderer modules — unchanged

---

## 8. Implementation Checklist

### 8.1 `_styles.py` — `FigureStyle`

- [ ] **S1:** Add `FigureStyle(VizStyle)` dataclass with fields: `width`, `height`, `background`, `auto_rotate`, `show_grid`, `show_axes`, `show_title`, `show_annotation`, `border_radius`
- [ ] **S2:** All fields default to `None`
- [ ] **S3:** Implement `FigureStyle.to_dict()` — include `style_type: "FigureStyle"`, omit `None`

### 8.2 `_figure.py` — `FigureConfig` (new file)

- [ ] **F1:** Create `py/pytanga/viz/_figure.py`
- [ ] **F2:** Define `FigureConfig` dataclass with `title`, `target`, `annotation`, `footer`, `background`, `browser_width`, `browser_height`
- [ ] **F3:** Implement `FigureConfig.to_dict()`

### 8.3 `scene.py` — SceneConfig extension

- [ ] **C1:** Add `figure: dict | None = None` field to `SceneConfig`
- [ ] **C2:** Include `"figure"` in `SceneConfig.to_dict()` when non-`None`

### 8.4 `visualizer.py` — Integration

- [ ] **V1:** Add `FigureConfig` storage (`self._figure_config`) in `__init__`
- [ ] **V2:** Accept `figure_config: FigureConfig | None` parameter in `__init__`
- [ ] **V3:** Coerce `title` / `annotation` kwargs into `FigureConfig` when no explicit `figure_config` is given
- [ ] **V4:** Add `figure_config` property returning `self._figure_config`
- [ ] **V5:** Add `default_figure_style` property (canonical `FigureStyle` instance)
- [ ] **V6:** Add `export_figure(path, *, style, overwrite)` method
- [ ] **V7:** Add `export_figure_html(*, style)` method returning `str`
- [ ] **V8:** Add `open_figure(*, style)` method — writes temp file + opens browser window
- [ ] **V9:** Pass figure style data into `scene_config.figure` when server starts
- [ ] **V10:** Update `set_title()` and `set_annotation()` to also update `self._figure_config`

### 8.5 `_figure_html.py` — Export Logic (new file)

- [ ] **E1:** Create `py/pytanga/viz/export/_figure_html.py`
- [ ] **E2:** Implement `render_export_figure(entities, labels, scene_config, figure_style) -> str`
- [ ] **E3:** Generated HTML snippet structure: `<div id="tanga-fig-{uuid}" style="...">` + `<script type="module">...</script>`
- [ ] **E4:** Inline renderer modules (same `_strip_imports` logic as `_html.py`)
- [ ] **E5:** Bootstrap adapter: mount to `#tanga-fig-xxx`, set renderer size from `FigureStyle`, apply `auto_rotate`, transparent background, show/hide overlays
- [ ] **E6:** Render footer markdown below the canvas if `footer` is provided
- [ ] **E7:** Include KaTeX `<link>` only when annotation/footer/labels contain `$` delimiters (optimization — scan text for `$`)

### 8.6 `figure_viewer.html` — Standalone Wrapper (new file)

- [ ] **W1:** Create `py/pytanga/viz/export/templates/figure_viewer.html`
- [ ] **W2:** Minimal HTML page: no toolbar, no status bar, just the figure snippet
- [ ] **W3:** `window.open()` target with `toolbar=no,location=no,status=no,menubar=no` flags plus exact width/height from `FigureStyle`

### 8.7 Frontend (`viewer.js`)

- [ ] **J1:** In `applySceneConfig()`: check `config.figure` presence
- [ ] **J2:** If `config.figure` present:
  - [ ] Set renderer size from `figure.width` × `figure.height`
  - [ ] Set canvas container dimensions
  - [ ] Apply `figure.background` to container (and `null` to scene background if transparent)
  - [ ] Set `controls.autoRotate` from `figure.auto_rotate`
  - [ ] Show/hide title overlay based on `figure.show_title`
  - [ ] Show/hide annotation panel based on `figure.show_annotation`
  - [ ] Show/hide grid and axes from `figure.show_grid` / `figure.show_axes`
- [ ] **J3:** If `config.figure` absent → render in full-viewport mode (existing behavior)

### 8.8 `__init__.py`

- [ ] **I1:** Export `FigureConfig` and `FigureStyle`

### 8.9 Tests

- [ ] **T1:** Test `FigureConfig.to_dict()` produces correct dict
- [ ] **T2:** Test `FigureStyle().to_dict()` returns `{"style_type": "FigureStyle"}`
- [ ] **T3:** Test `FigureStyle(width=1024, auto_rotate=True).to_dict()` includes only set fields
- [ ] **T4:** Test `viz.figure_config.title` auto-completes
- [ ] **T5:** Test `viz.default_figure_style.width` is mutable
- [ ] **T6:** Test `viz.export_figure("test.html")` creates valid HTML snippet
- [ ] **T7:** Test exported snippet contains `<div id="tanga-fig-` and `<script type="module">`
- [ ] **T8:** Test exported snippet does NOT contain `<html>`, `<head>`, or `<body>` tags
- [ ] **T9:** Test `FigureConfig` coercion: `Visualizer(title="X", annotation="Y")` → `figure_config.title == "X"`, `figure_config.annotation == "Y"`
- [ ] **T10:** Test `figure_config` parameter overrides kwargs
- [ ] **T11:** All existing tests pass (no regressions in viz tests, export smoke tests)

### 8.10 Smoke / Manual Verification

- [ ] **M1:** Export figure → paste into a reveal.js slide → 3D scene renders at correct size
- [ ] **M2:** Transparent background → slide background visible behind the figure
- [ ] **M3:** `auto_rotate=True` → camera rotates passively
- [ ] **M4:** Footer markdown rendered with KaTeX formulas
- [ ] **M5:** `show_title=False` → title is hidden
- [ ] **M6:** `show_annotation=False` → annotation panel is hidden
- [ ] **M7:** Orbit controls still work (rotate/pan/zoom)
- [ ] **M8:** Labels with KaTeX render correctly
- [ ] **M9:** `viz.open_figure()` opens a standalone window at the right size
- [ ] **M10:** Exported snippet does not leak styles to parent page
- [ ] **M11:** Browser console has no errors

---

## 9. Verification Checklist

- [ ] `FigureStyle` dataclass exists with all 9 fields and `to_dict()`
- [ ] `FigureConfig` dataclass exists with all 7 fields and `to_dict()`
- [ ] `Visualizer.figure_config` property returns mutable `FigureConfig`
- [ ] `Visualizer.default_figure_style` property returns mutable `FigureStyle`
- [ ] `viz.export_figure("figure.html")` produces a valid HTML snippet
- [ ] Snippet contains `<div id="tanga-fig-` and `<script type="module">`
- [ ] Snippet does NOT contain `<html>`, `<head>`, `<body>` tags
- [ ] Snippet uses scoped CSS only (no global style resets)
- [ ] `SceneConfig.to_dict()` includes `"figure"` key when configured
- [ ] Live viewer applies figure mode when `config.figure` is present
- [ ] Live viewer falls back to full-viewport when `config.figure` is absent
- [ ] `viz.open_figure()` opens a browser window at configured dimensions
- [ ] Footer is rendered as markdown with KaTeX math below the canvas
- [ ] All existing tests pass (no regressions)

---

## 10. Usage Examples

### 10.1 Basic Figure Export

```python
from pytanga.viz import Visualizer, FigureStyle
from pytanga.geometry import Point, Sphere

viz = Visualizer(
    title="My Construction",
    annotation="## Step 1\n\n$e^{i\\pi} = -1$",
)
viz.add(Sphere(Point(0, 0, 0), 2), wireframe=True, opacity=0.4, label="$S_1$")

# Export as a presentation-ready snippet
viz.export_figure(
    "my_figure.html",
    style=FigureStyle(
        width=800, height=600, background="transparent",
        auto_rotate=True, border_radius="8px",
    ),
)
```

### 10.2 With Footer

```python
viz.figure_config.footer = "**Figure 1:** A sphere of radius $r=2$ centered at the origin."
viz.figure_config.target = "#my-slide"
viz.export_figure("figure_with_caption.html")
```

### 10.3 Standalone Window Preview

```python
viz.open_figure(style=FigureStyle(width=1024, height=768, auto_rotate=True))
```

### 10.4 Programmatic Snippet Generation

```python
snippet = viz.export_figure_html(style=FigureStyle(width=600, height=400))
# Insert snippet into a template or notebook
```

---

## 11. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **11** | `_html.py` full-page export is unchanged. `_figure_html.py` follows the same pattern (strip imports, concatenate modules, append adapter) but produces a snippet instead of a full document. |
| **12** | Title, annotation, and KaTeX rendering are reused in figure exports — toggled via `FigureStyle.show_title` / `.show_annotation`. Footer uses the same `marked.parse()` + `renderMathInElement()` pipeline. |
| **10** | Examples should include a `demo_figure_export.py` script. |
| **9** | Docs should document `FigureConfig`, `FigureStyle`, `export_figure()`, `open_figure()`. |
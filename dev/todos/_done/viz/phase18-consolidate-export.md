# Phase 18 — Consolidate Export Bootstrap Code

**Prerequisites:** Phase 17 (animated HTML figure export), Phase 13 (figure export), Phase 11 (HTML export), Phase 12 (title & annotation)

**Goal:** Eliminate ~800 lines of duplicated JS bootstrap generation code across two vertical dimensions:

1. **Static vs. animated** — the four JS bootstrap generators share ~80% of their scene setup, entity creation, label handling, camera auto-fit, title/annotation, and render loop logic. Only the **data source** (embedded JSON vs. `window.__TANGA_ANIMATION__`) and **playback engine** (absent vs. present) vary.

2. **Full-page vs. figure snippet** — each pair (static full-page + static figure, animated full-page + animated snippet) shares the same rendering logic but differs only in **HTML framing** (`<!DOCTYPE html>` vs. `<div>` snippet) and **DOM attachment** (`document.body` vs. `#tanga-fig-xxx`).

The refactor introduces a shared **JS code generator** module (`_bootstrap_core.py`) with composable Python functions returning JS code strings. Each of the four export paths composes these building blocks with their specific parameters, eliminating the duplication.

Additionally, this phase fixes the bug identified in the Phase 17 review: the animated figure snippet export does not render title or annotation overlays. After the refactor, all four paths use the same `js_title_overlay()` and `js_annotation_panel()` functions, making the bug impossible.

**Status:** ✅ Complete (all checkboxes)


---

## 1. Motivation

### 1.1 Two Orthogonal Duplication Axes

| | Static | Animated |
|---|---|---|
| **Full-Page** | `_BOOTSTRAP_ADAPTER` in `_html.py` (~230 lines) | `_fullpage_animated_adapter()` in `_animated_figure.py` (~250 lines) |
| **Figure Snippet** | `_figure_adapter()` in `_figure_html.py` (~270 lines) | `_figure_animated_adapter()` in `_animated_figure.py` (~260 lines) |

**Horizontal duplication (static vs. animated):** Each animated adapter is essentially a copy of its static counterpart with animation playback logic added and data source changed.

**Vertical duplication (full-page vs. figure):** Each figure adapter is a copy of its full-page counterpart with the container changed from `document.body` to `#tanga-fig-xxx`, dimensions from full-viewport to fixed `width`×`height`, and title/annotation positioning from `position:fixed` to position within the container.

### 1.2 Concrete Overlap — Every Adapter Does These Identical Steps

1. Import Three.js addons (`OrbitControls`, `CSS2DRenderer`, `CSS2DObject`)
2. Scene creation (`THREE.Scene` + background color)
3. Camera creation (`PerspectiveCamera` with FOV, near, far)
4. Renderer creation (`WebGLRenderer` with antialias)
5. CSS2D renderer creation + styling
6. OrbitControls setup
7. Lighting (ambient + two directionals)
8. Grid helper (conditional)
9. Axes helper (conditional)
10. Title overlay (DOM element creation)
11. Annotation panel (markdown + KaTeX rendering)
12. Entity mesh creation loop
13. Auto-fit camera from bounding box
14. Label CSS2D object creation loop
15. Resize handling (conditional)
16. Render loop (`requestAnimationFrame`)

The **only differences** are:
- Data source: embedded JSON in `<script>` tags vs. `window.__TANGA_ANIMATION__`
- Container: `document.body` vs. `#tanga-fig-{uuid}`
- Dimensions: `window.innerWidth/Height` vs. configurable `w`×`h`
- Background: from `SceneConfig.background_color` vs. from `FigureConfig.background`
- Title positioning: `position:fixed` vs. `position:absolute` within container
- Animation playback engine: absent vs. present
- Resize handler: always present for full-page, only for `responsive=True` in figure

### 1.3 Bug Fix: Missing Title & Annotation in Animated Figure

As identified in the Phase 17 review, `_figure_animated_adapter()` does not render title or annotation because it never reads those fields from `figure_config`/`figure_style`. After the refactor, all four adapters call the same `js_title_overlay()` and `js_annotation_panel()` shared functions, guaranteeing consistent behavior.

---

## 2. Design: `_bootstrap_core.py` — Shared JS Code Generator

### 2.1 Module Location

`py/pytanga/viz/export/_bootstrap_core.py` (new)

### 2.2 Composable Functions

Each function takes configuration dicts/values and returns a JS code string (lines of JavaScript). Functions are idempotent — no shared state, no side effects.

```python
# py/pytanga/viz/export/_bootstrap_core.py

from __future__ import annotations

from typing import Any


def js_imports() -> str:
    """Three.js addon imports."""
    return """import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';"""


def js_scene_setup(
    *,
    bg_color: str,
    container_expr: str,         # JS expression for the container DOM element, e.g. "document.body" or "figContainer"
    renderer_var: str,           # JS variable name for the WebGLRenderer, e.g. "figRenderer"
    label_renderer_var: str,     # JS variable name for CSS2DRenderer, e.g. "figLabelRenderer"
    camera_var: str,             # JS variable name for the camera, e.g. "figCamera"
    controls_var: str,           # JS variable name for OrbitControls, e.g. "figControls"
    scene_var: str,              # JS variable name for the scene, e.g. "figScene"
    width_expr: str,             # JS expression for renderer width, e.g. "window.innerWidth" or "800"
    height_expr: str,            # JS expression for renderer height
    cam_fov: float,
    cam_pos: tuple,
    cam_target: tuple,
    cam_near: float,
    cam_far: float,
    auto_rotate: bool,
    show_grid: bool,
    show_axes: bool,
    space_extent: float,
    append_to: str,              # JS expression for where to append renderer DOM elements, e.g. "document.body" or "figContainer"
    pixel_ratio_expr: str = "window.devicePixelRatio",
) -> str:
    """Generate JS for scene, camera, renderers, controls, lighting, grid, axes."""
    ...


def js_title_overlay(
    *,
    title: str,
    container_expr: str,
    positioning: str = "fixed",  # "fixed" for full-page, "absolute" for figure
    show_title: bool = True,
    z_index: int = 5,
) -> str:
    """Generate JS for creating a title DOM element.

    Returns an empty string if ``title`` is empty or ``show_title`` is False.
    """
    ...


def js_annotation_panel(
    *,
    annotation_md: str,
    container_expr: str,
    positioning: str = "fixed",
    show_annotation: bool = True,
    z_index: int = 5,
) -> str:
    """Generate JS for creating a markdown annotation panel.

    Uses ``marked.parse()`` + ``renderMathInElement()``.
    Returns an empty string if ``annotation_md`` is empty or ``show_annotation`` is False.
    """
    ...


def js_footer(
    *,
    footer_md: str,
    container_expr: str,
) -> str:
    """Generate JS for creating a footer element below the canvas.

    Returns an empty string if ``footer_md`` is empty.
    """
    ...


def js_entity_creation(
    *,
    entities_expr: str,       # JS expression yielding the entities array, e.g. "figEntities" or "initial"
    mesh_map_var: str,        # JS variable name for the mesh map, e.g. "figMeshMap"
    scene_var: str,           # JS variable name for the scene
    layer_dispatch: bool = True,  # whether to dispatch on obj.layer (future Phase 8a) vs. direct createEntityMesh
) -> str:
    """Generate JS for entity/operator mesh creation loop."""
    ...


def js_label_creation(
    *,
    labels_expr: str,         # JS expression yielding labels array
    mesh_map_var: str,
    scene_var: str,
    use_label_objects_map: bool = False,  # if True, stores labels in "labelObjects" Map
    label_objects_map_var: str = "labelObjects",
) -> str:
    """Generate JS for label CSS2D object creation loop."""
    ...


def js_autofit_camera(
    *,
    mesh_map_var: str,
    camera_var: str,
    controls_var: str,
    cam_explicit: bool,
) -> str:
    """Generate JS for auto-fit camera from entity bounding box.

    Returns an empty string if ``cam_explicit`` is True.
    """
    ...


def js_render_loop(
    *,
    renderer_var: str,
    label_renderer_var: str,
    scene_var: str,
    camera_var: str,
    controls_var: str,
    extra_per_frame: str = "",  # additional JS to run per frame (e.g. animation playback)
) -> str:
    """Generate JS for the requestAnimationFrame render loop."""
    ...


def js_resize_handler(
    *,
    renderer_var: str,
    label_renderer_var: str,
    camera_var: str,
    width_expr: str,
    height_expr: str,
    conditional: bool = False,  # if True, only sets up resize when needed
) -> str:
    """Generate JS for window resize handler.

    If ``conditional`` is True, the handler reads size from the container
    element instead of ``window.innerWidth/Height`` (for responsive figures).
    """
    ...


def js_animation_playback(
    *,
    frames_var: str,           # JS expression for frames array, e.g. "frames"
    mesh_map_var: str,
    fps: int,
    loop: bool,
    show_controls: bool,
    controls_html_id: str,     # e.g. "tanga-controls"
    total_duration_expr: str,  # JS expression for total animation duration
    scene_var: str,
) -> str:
    """Generate JS for the animation playback engine (play/pause/scrub/speed/loop).

    Returns an empty string if frames are empty (no animation).
    """
    ...


def js_controls_ui(
    *,
    html_id: str,
    position_css: str = "",
) -> str:
    """Generate both the HTML and JS for playback controls (play/pause, scrub, speed, loop).

    Returns an empty string if ``show_controls`` is False.
    """
    ...
```

### 2.3 How the Four Adapters Compose

#### Static Full-Page (`_html.py` `_BOOTSTRAP_ADAPTER`)

```python
def _build_static_fullpage_adapter(scene_config, scene_data_json) -> str:
    sc = scene_config
    parts = [
        js_imports(),
        f"const sceneData = {scene_data_json};",
        "const entities = sceneData.entities || [];",
        'const labels = sceneData.labels || [];',
        js_scene_setup(container_expr="document.body", append_to="document.body",
                       bg_color=sc["background_color"], ...),
        js_title_overlay(title=sc["title"], container_expr="document.body", positioning="fixed"),
        js_annotation_panel(annotation_md=sc["annotation"], container_expr="document.body", positioning="fixed"),
        js_entity_creation(entities_expr="entities", mesh_map_var="meshMap", scene_var="scene"),
        js_autofit_camera(...),
        js_label_creation(labels_expr="labels", ...),
        js_render_loop(...),
        js_resize_handler(conditional=False),
    ]
    return "\n\n".join(parts)
```

#### Static Figure (`_figure_html.py` `_figure_adapter()`)

```python
def _build_static_figure_adapter(fig_id, scene_json, figure_style, figure_config) -> str:
    fs = figure_style
    fc = figure_config
    parts = [
        js_imports(),
        f"const figData = {scene_json};",
        "const figEntities = figData.entities || [];",
        'const figLabels = figData.labels || [];',
        js_scene_setup(container_expr=f"document.getElementById('{fig_id}')",
                       append_to=f"figContainer",
                       bg_color=fc.get("background", "#1a1a2e"),
                       width_expr=str(fs.get("width", 800)),
                       height_expr=str(fs.get("height", 600)),
                       ...),
        js_title_overlay(title=fc.get("title", ""),
                         container_expr="figContainer",
                         positioning="absolute",
                         show_title=fs.get("show_title", True)),
        js_annotation_panel(annotation_md=fc.get("annotation", ""),
                            container_expr="figContainer",
                            positioning="absolute",
                            show_annotation=fs.get("show_annotation", True)),
        js_footer(footer_md=fc.get("footer", ""), container_expr="figContainer"),
        js_entity_creation(entities_expr="figEntities", mesh_map_var="figMeshMap", scene_var="figScene"),
        js_autofit_camera(...),
        js_label_creation(labels_expr="figLabels", ...),
        js_render_loop(...),
        js_resize_handler(conditional=(fs.get("responsive", False))),
    ]
    return "\n\n".join(parts)
```

#### Animated Full-Page (`_animated_figure.py` `_fullpage_animated_adapter()`)

```python
def _build_animated_fullpage_adapter(fig_id, recording_data, scene_config, ...) -> str:
    sc = scene_config
    parts = [
        js_imports(),
        _GET_ANIM_DATA_JS,  # existing helper
        js_scene_setup(container_expr="document.body", append_to="document.body",
                       bg_color=sc["background_color"], ...),
        js_title_overlay(title=sc.get("title", ""), container_expr="document.body", positioning="fixed"),
        js_annotation_panel(annotation_md=sc.get("annotation", ""), container_expr="document.body", positioning="fixed"),
        js_entity_creation(entities_expr="initial", mesh_map_var="figMeshMap", scene_var="figScene"),
        js_autofit_camera(...),
        js_label_creation(labels_expr="initial.filter(o => o.kind === 'label')", ...),
        js_animation_playback(frames_var="frames", mesh_map_var="figMeshMap", ...),
        js_controls_ui(html_id="tanga-controls"),
        js_render_loop(extra_per_frame="_updateScrubBar();"),
        js_resize_handler(conditional=False),
    ]
    return "\n\n".join(parts)
```

#### Animated Figure (`_animated_figure.py` `_figure_animated_adapter()`)

```python
def _build_animated_figure_adapter(fig_id, recording_data, figure_style, figure_config, ...) -> str:
    fs = figure_style
    fc = figure_config
    parts = [
        js_imports(),
        _GET_ANIM_DATA_JS,
        js_scene_setup(container_expr=f"document.getElementById('{fig_id}')",
                       append_to="figContainer",
                       bg_color=fc.get("background", "#1a1a2e"),
                       width_expr=str(fs.get("width", 800)),
                       height_expr=str(fs.get("height", 600)),
                       ...),
        js_title_overlay(title=fc.get("title", ""),        # ← NEW (was missing before)
                         container_expr="figContainer",
                         positioning="absolute",
                         show_title=fs.get("show_title", True)),
        js_annotation_panel(annotation_md=fc.get("annotation", ""),  # ← NEW (was missing before)
                            container_expr="figContainer",
                            positioning="absolute",
                            show_annotation=fs.get("show_annotation", True)),
        js_footer(footer_md=fc.get("footer", ""), container_expr="figContainer"),  # ← NEW
        js_entity_creation(entities_expr="initial", mesh_map_var="figMeshMap", scene_var="figScene"),
        js_autofit_camera(...),
        js_label_creation(labels_expr="initial.filter(o => o.kind === 'label')", ...),
        js_animation_playback(frames_var="frames", mesh_map_var="figMeshMap", ...),
        js_controls_ui(html_id="tanga-controls"),
        js_render_loop(extra_per_frame="_updateScrubBar();"),
        js_resize_handler(conditional=(fs.get("responsive", False))),
    ]
    return "\n\n".join(parts)
```

---

## 3. HTML Template Unification

### 3.1 Current State

Each export path generates its own HTML template with inline CDN links, import maps, and script tags:

| Path | Template Generation |
|------|-------------------|
| Static full-page | `_html.py` uses `export_viewer.html` template with placeholder replacements |
| Static figure | `_figure_html.py` `render_export_figure()` generates inline |
| Animated full-page | `_animated_figure.py` `render_export_animated_html()` generates inline |
| Animated figure | `_animated_figure.py` `render_export_animated_figure()` generates inline |

### 3.2 Proposed: Shared Template Helpers

Two meta-functions generate the HTML wrapper:

```python
# _bootstrap_core.py

def html_fullpage_template(
    *,
    title: str,
    bg_color: str,
    katex_css: str,           # "<link>..." or ""
    extra_head_scripts: str,  # marked, KaTeX script tags
    anim_decompress_js: str,  # decompression bootstrapper (or "")
) -> str:
    """Return a full-page HTML document (``<!DOCTYPE html>`` ... ``</html>``)."""
    ...

def html_snippet_template(
    *,
    extra_head_scripts: str,
    katex_css: str,
    import_map_json: str,
    anim_embed: str,           # animation data script tag(s)
    anim_decompress_js: str,
    container_div: str,        # the <div id="tanga-fig-xxx" ...> element
    bootstrap_js: str,         # the concatenated renderer modules + adapter
) -> str:
    """Return an HTML snippet (``<div>`` + ``<script type="module">``)."""
    ...
```

The existing `render_export_*` functions in `_html.py`, `_figure_html.py`, and `_animated_figure.py` become thin wrappers that call these shared template functions with their specific parameters.

---

## 4. Implementation Strategy

### 4.1 Phase Order

1. **Create `_bootstrap_core.py`** with all composable JS generator functions.
2. **Rewrite the four adapters** to use `_bootstrap_core.py` functions, verifying each adapter produces identical output to the pre-refactor version.
3. **Simplify the existing export renderers** (`_html.py`, `_figure_html.py`, `_animated_figure.py`) by removing the large js adapter code blocks and replacing them with calls to the composable functions.

### 4.2 Verification Approach

For each adapter, before and after the refactor:
- Export a scene and compare the JS bootstrap code with `diff` to verify no behavioral changes.
- Manual smoke test each export format in the browser.

### 4.3 What Stays the Same

- All public API methods (`SceneExporter.export_html`, `.export_figure`, `.export_animated_figure`, `.export_animated_html`)
- Output HTML format (identical JS code generated)
- `_strip_imports()` function (kept in `_figure_html.py`, imported by `_animated_figure.py`)
- `_RENDERER_FILES` list (kept in `_figure_html.py`)

---

## 5. Files to Create / Modify

### 5.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/export/_bootstrap_core.py` | ~15 composable JS generator functions + 2 HTML template helpers + `_escape_html`, `_escape_js` utilities |

### 5.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/export/_html.py` | Replace `_BOOTSTRAP_ADAPTER` string with call to `_bootstrap_core.py` functions; simplify `render_export_html()`; keep `_strip_imports`, `_RENDERER_FILES`, `render_export_html()` |
| `py/pytanga/viz/export/_figure_html.py` | Replace `_figure_adapter()` with call to composable functions from `_bootstrap_core.py`; simplify `render_export_figure()` |
| `py/pytanga/viz/export/_animated_figure.py` | Replace `_figure_animated_adapter()` and `_fullpage_animated_adapter()` with calls to composable functions; simplify `render_export_animated_figure()` and `render_export_animated_html()`; remove shared JS snippets (`_GET_ANIM_DATA_JS`, `_CREATE_LABEL_FIG_JS`, `_CREATE_LABEL_FULL_JS`, `_CONTROLS_HTML`, `_CONTROLS_JS`, `_ANNOTATION_CONTROLS_REPOSITION_JS`) that become redundant |

### 5.3 Files NOT Modified

- `py/pytanga/viz/export/_exporter.py` — unchanged (public API stays the same)
- `py/pytanga/viz/export/_gltf.py` — unchanged
- `py/pytanga/viz/export/_gltf_primitives.py` — unchanged
- `py/pytanga/viz/export/_animation_recording.py` — unchanged
- `py/pytanga/viz/export/_screenshot.py` — unchanged
- `py/pytanga/viz/export/_capture.py` — unchanged
- All JS renderer modules — unchanged
- `py/pytanga/viz/visualizer.py` — unchanged
- `py/pytanga/viz/scene.py` — unchanged
- `py/pytanga/viz/__init__.py` — unchanged

---

## 6. Implementation Checklist

### 6.1 `_bootstrap_core.py` — Shared JS Generator Functions

- [ ] **B1:** Create `py/pytanga/viz/export/_bootstrap_core.py`
- [ ] **B2:** Implement `js_imports()` — Three.js addon imports
- [ ] **B3:** Implement `js_scene_setup()` — scene, camera, renderers, controls, lighting, grid, axes (replaces ~60 duplicated lines per adapter)
- [ ] **B4:** Implement `js_title_overlay()` — title DOM element creation with configurable positioning (replaces ~20 duplicated lines per adapter)
- [ ] **B5:** Implement `js_annotation_panel()` — markdown + KaTeX panel creation (replaces ~35 duplicated lines per adapter)
- [ ] **B6:** Implement `js_footer()` — footer DOM element below canvas
- [ ] **B7:** Implement `js_entity_creation()` — entity mesh creation loop (replaces ~10 duplicated lines per adapter)
- [ ] **B8:** Implement `js_label_creation()` — label CSS2D object creation loop (replaces ~45 duplicated lines per adapter)
- [ ] **B9:** Implement `js_autofit_camera()` — bounding box auto-fit logic (replaces ~20 duplicated lines per adapter)
- [ ] **B10:** Implement `js_render_loop()` — requestAnimationFrame render loop (replaces ~7 duplicated lines per adapter)
- [ ] **B11:** Implement `js_resize_handler()` — window resize listener (replaces ~15 duplicated lines per adapter, with conditional support)
- [ ] **B12:** Implement `js_animation_playback()` — play/pause/scrub/speed/loop engine (replaces ~120 lines duplicated between two animated adapters)
- [ ] **B13:** Implement `js_controls_ui()` — HTML + JS for playback controls UI (replaces `_CONTROLS_HTML` + `_CONTROLS_JS`)
- [ ] **B14:** Implement `html_fullpage_template()` — full-page HTML document wrapper
- [ ] **B15:** Implement `html_snippet_template()` — HTML snippet wrapper
- [ ] **B16:** Implement shared utility helpers: `_escape_html(text)`, `_escape_js(text)`, `_format_js_array(items)`, `_format_js_bool(val)`

### 6.2 `_html.py` — Refactor Static Full-Page Adapter

- [ ] **H1:** Replace `_BOOTSTRAP_ADAPTER` (230-line string) with a `_build_static_fullpage_adapter()` function that composes `_bootstrap_core.py` functions
- [ ] **H2:** Replace inline template in `render_export_html()` with `html_fullpage_template()` call
- [ ] **H3:** Verify: generated HTML is byte-identical to pre-refactor version (or functionally identical if cosmetic whitespace differs)

### 6.3 `_figure_html.py` — Refactor Static Figure Adapter

- [ ] **F1:** Replace `_figure_adapter()` body (~270 lines of f-string code) with `_build_static_figure_adapter()` composing `_bootstrap_core.py` functions
- [ ] **F2:** Replace inline HTML template in `render_export_figure()` with `html_snippet_template()` call
- [ ] **F3:** Verify: generated HTML snippet is functionally identical to pre-refactor version

### 6.4 `_animated_figure.py` — Refactor Both Animated Adapters

- [ ] **A1:** Replace `_fullpage_animated_adapter()` body (~250 lines) with `_build_animated_fullpage_adapter()` composing `_bootstrap_core.py` functions
- [ ] **A2:** Replace `_figure_animated_adapter()` body (~260 lines) with `_build_animated_figure_adapter()` composing `_bootstrap_core.py` functions — **this fixes the missing title/annotation bug**
- [ ] **A3:** Replace inline HTML template in `render_export_animated_html()` with `html_fullpage_template()` call
- [ ] **A4:** Replace inline HTML template in `render_export_animated_figure()` with `html_snippet_template()` call
- [ ] **A5:** Remove now-redundant shared JS snippets: `_GET_ANIM_DATA_JS`, `_CREATE_LABEL_FIG_JS`, `_CREATE_LABEL_FULL_JS`, `_CONTROLS_HTML`, `_CONTROLS_JS`, `_ANNOTATION_CONTROLS_REPOSITION_JS` (moved to `_bootstrap_core.py`)
- [ ] **A6:** Remove `_embed_animation_data()` and `_katex_css_if_needed()` (moved to `_bootstrap_core.py`)
- [ ] **A7:** Remove `_ANIMATION_DECOMPRESS_JS` constant (moved to `_bootstrap_core.py`)

### 6.5 Tests

- [ ] **T1:** Test `js_title_overlay(title="My Title", positioning="fixed")` produces correct JS with `position:fixed`
- [ ] **T2:** Test `js_title_overlay(title="My Title", positioning="absolute")` produces correct JS with `position:absolute`
- [ ] **T3:** Test `js_title_overlay(title="", ...)` returns empty string
- [ ] **T4:** Test `js_title_overlay(show_title=False, ...)` returns empty string
- [ ] **T5:** Test `js_annotation_panel()` with markdown containing `$e=mc^2$` produces `marked.parse()` + `renderMathInElement()` calls
- [ ] **T6:** Test `js_annotation_panel(annotation_md="")` returns empty string
- [ ] **T7:** Test `js_autofit_camera(cam_explicit=True)` returns empty string
- [ ] **T8:** Test `js_resize_handler(conditional=True)` produces conditional resize logic reading from container
- [ ] **T9:** Test `js_animation_playback(frames=[], ...)` returns empty string (no animation)
- [ ] **T10:** Test `js_controls_ui(show_controls=False)` returns empty string
- [ ] **T11:** Test `html_fullpage_template()` output contains `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`
- [ ] **T12:** Test `html_snippet_template()` output does NOT contain `<html>`, `<head>`, `<body>`
- [ ] **T13:** Test static full-page export produces identical JS bootstrap as before
- [ ] **T14:** Test static figure export produces identical JS bootstrap as before
- [ ] **T15:** Test animated full-page export produces identical JS bootstrap as before
- [ ] **T16:** Test animated figure export includes title and annotation rendering (bug fix verification)
- [ ] **T17:** All existing tests pass (no regressions)

### 6.6 Smoke / Manual Verification

- [ ] **M1:** `exporter.export_html("test.html")` — opens in browser, all entities render, title/annotation visible
- [ ] **M2:** `exporter.export_figure("test.html")` — snippet renders correctly when embedded in a page, title/annotation visible
- [ ] **M3:** `exporter.export_animated_html("test.html")` — opens in browser, animation plays, title/annotation visible
- [ ] **M4:** `exporter.export_animated_figure("test.html")` — snippet renders correctly, animation plays, **title and annotation visible** (bug fix)
- [ ] **M5:** `exporter.export_figure("test.html", style=FigureStyle(show_title=False))` — title hidden
- [ ] **M6:** `exporter.export_figure("test.html", style=FigureStyle(show_annotation=False))` — annotation hidden
- [ ] **M7:** Browser console has no errors
- [ ] **M8:** Exported files work when opened from a different directory/machine

---

## 7. Line Count Summary

| File | Before | After | Delta |
|------|--------|-------|-------|
| `_html.py` | ~401 | ~120 | -281 |
| `_figure_html.py` | ~506 | ~200 | -306 |
| `_animated_figure.py` | ~1196 | ~350 | -846 |
| `_bootstrap_core.py` (new) | 0 | ~550 | +550 |
| **Total** | ~2103 | ~1220 | **-883** |

The four adapters collapse from ~1000 lines of duplicated JS code to ~120 lines of composable function calls each. The ~550-line `_bootstrap_core.py` is pure utility code with zero duplication.

---

## 8. Verification Checklist

- [ ] `_bootstrap_core.py` contains all 15 composable JS generator functions
- [ ] Each function returns a string of syntactically valid JavaScript
- [ ] Four adapters produce identical JS bootstrap code to pre-refactor versions
- [ ] Animated figure export now includes title and annotation overlays (bug fix)
- [ ] `_html.py` no longer contains the 230-line `_BOOTSTRAP_ADAPTER` string
- [ ] `_figure_html.py` `_figure_adapter()` is <40 lines (calls composable functions)
- [ ] `_animated_figure.py` no longer contains 6 shared JS snippet constants
- [ ] `_animated_figure.py` `_figure_animated_adapter()` is <40 lines
- [ ] `_animated_figure.py` `_fullpage_animated_adapter()` is <40 lines
- [ ] All `render_export_*()` functions use shared HTML template helpers
- [ ] All existing tests pass
- [ ] No changes to public API (`SceneExporter` methods unchanged)
- [ ] Browser console has no errors

---

## 9. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **11** | `_html.py` is simplified — `_BOOTSTRAP_ADAPTER` string replaced by composable functions |
| **13** | `_figure_html.py` is simplified — `_figure_adapter()` body replaced |
| **12** | Title and annotation rendering moves to shared `js_title_overlay()` / `js_annotation_panel()` — no more duplication across four paths |
| **17** | `_animated_figure.py` is simplified — both animated adapters replaced; title/annotation bug fixed |
| **8a** | Future unified overlay layer dispatch can be added to `js_entity_creation()` and `js_label_creation()` in one place |
| **8b** | Future style_type string changes update in one place (`_bootstrap_core.py`) |
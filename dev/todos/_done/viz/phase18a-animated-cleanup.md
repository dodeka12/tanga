# Phase 18a — Animated Bootstrap Cleanup & File Split

**Prerequisites:** Phase 18 (consolidate export bootstrap code)

**Goal:** Complete the Phase 18 refactor by (1) moving remaining inline JS templates from `_animated_figure.py` into shared `_bootstrap_core.py` functions, (2) eliminating cross-file duplication discovered during audit, and (3) splitting the oversized `_bootstrap_core.py` (1173 lines) into smaller modules organized by responsibility.

**Status:** ✅ Complete (all checkboxes)


---

## 1. Remaining JS Templates in `_animated_figure.py`

Both `_build_animated_figure_adapter()` and `_build_animated_fullpage_adapter()` still contain large inline JS blocks that should be in the `_bootstrap/` shared modules. This is the primary motivation for Phase 18a.

### 1.1 `_createLabel` / `_createLabelFull` — ~45 lines each, 90% identical

| Aspect | `_createLabel` (figure adapter) | `_createLabelFull` (full-page adapter) |
|--------|----------------------------------|----------------------------------------|
| Lines | 43 | 45 |
| **Only difference** | No `labelObjects` storage | `labelObjects.set(lbl.id, labelObj)` at end |

**Plan:** Replace both with a single `js_animated_label_function(label_map_var: str = "")` in `_bootstrap/_animation.py`. When `label_map_var` is non-empty (e.g. `"labelObjects"`), the function appends the Map storage line. The function name is always `_createLabel` at the JS level.

### 1.2 `_animated_playback_engine()` — 110 lines, already parametrized

This private function in `_animated_figure.py` generates `applyFrameUpdate` + `_figAnimate` JS. It already accepts `scene_var` and `label_objects_map_var` as parameters, but hardcodes these names that are **consistent between both adapters**: `figMeshMap`, `frames`, `isPlaying`, `currentFrame`, `startTime`, `totalDuration`, `figControls`, `figRenderer`, `figLabelRenderer`, `figScene`, `figCamera`, `_updatePlayBtn()`, `_updateScrubBar()`.

**Plan:** Move to `_bootstrap/_animation.py` as `js_animated_render_loop()`. Delete the existing unused `js_animation_playback()` function from the old `_bootstrap_core.py` (same 110-line body, but never called by any adapter).

### 1.3 Animation State Block — 8 lines, verbatim identical

Both adapters duplicate:

```js
// State
let isPlaying = false;
let currentFrame = -1;
let startTime = 0;
let totalDuration = animData.frame_count > 0
    ? animData.frame_count / fps
    : 0;
```

**Plan:** `js_animation_state()` in `_bootstrap/_animation.py`. Takes no parameters.

### 1.4 Animation Data Init Block — 6 lines, nearly identical

Both adapters duplicate:

```js
const animData = _getAnimData();
const fps = animData.fps || {fps};
const frames = animData.frames || [];
const initial = animData.initial_state || [];
const figMeshMap = new Map();
```

The full-page adapter additionally has `const labelObjects = new Map();`.

**Plan:** `js_animation_data_init(fps: int, extra_maps: str = "")` in `_bootstrap/_animation.py`. `extra_maps` is appended as additional JS (e.g. `"\nconst labelObjects = new Map();"`).

### 1.5 Resize Handler — adapters don't use existing `js_resize_handler()`

| Adapter | Current Behavior |
|---------|-----------------|
| Animated figure | Inline 7-line conditional resize (only if `responsive`) |
| Animated full-page | Inline 6-line resize (always present) |

The `js_resize_handler()` function in `_bootstrap/_scene.py` already supports `conditional` mode. The adapters just aren't calling it.

**Plan:** Replace both inline resize blocks with `js_resize_handler()` calls.

### 1.6 Auto-Fit Camera — figure adapter doesn't use existing `js_autofit_camera()`

`_build_animated_figure_adapter()` has 18 lines of inline auto-fit JS. The full-page adapter correctly calls `js_autofit_camera()`.

**Plan:** Replace inline auto-fit in figure adapter with `js_autofit_camera()` call.

### 1.7 Summary of Lines Reducible from `_animated_figure.py`

| Item | Lines replaced |
|------|---------------|
| `_createLabel` / `_createLabelFull` → `js_animated_label_function()` | ~90 |
| `_animated_playback_engine()` → `js_animated_render_loop()` | ~110 |
| Animation state → `js_animation_state()` | ~16 |
| Animation data init → `js_animation_data_init()` | ~12 |
| Resize handler → `js_resize_handler()` | ~13 |
| Auto-fit camera → `js_autofit_camera()` | ~18 |
| **Total** | **~260** |

After changes: `_animated_figure.py` drops from ~798 to ~540 lines. Each adapter builder becomes a ~50-60 line composition.

---

## 2. Cross-File Duplication Audit

### 2.1 `_strip_imports()` — Identical in `_html.py` and `_figure_html.py`

Two identical 60-line implementations. `_animated_figure.py` already imports from `_figure_html.py`:

```python
from pytanga.viz.export._figure_html import _strip_imports
```

**Plan:** Move `_strip_imports()` to `_bootstrap/_html.py`. Both `_html.py` and `_figure_html.py` import from there via `_bootstrap/__init__.py`. Remove the duplicates from both files.

### 2.2 `_RENDERER_FILES` — Identical List in `_html.py` and `_figure_html.py`

An identical 21-item `List[Path]`. `_animated_figure.py` already imports from `_figure_html.py`:

```python
from pytanga.viz.export._figure_html import _RENDERER_FILES as _FIG_RENDERER_FILES
```

**Plan:** Move `_RENDERER_FILES` to `_bootstrap/_html.py`. All three files import from there via `_bootstrap/__init__.py`. Define it once.

### 2.3 Bootstrap Concatenation Pattern — Identical in 4 Functions

Every file repeats the same pattern:

```python
parts: list[str] = []
parts.append("import * as THREE from 'three';")

for path in _RENDERER_FILES:
    src = path.read_text()
    src = _strip_imports(src)
    parts.append(src)

parts.append(adapter_js)
return "\n\n".join(parts)
```

This appears in:
- `_html.py` `_generate_bootstrap()` (lines 83-100)
- `_figure_html.py` `_generate_figure_bootstrap()` (lines 150-161)
- `_animated_figure.py` `_generate_animated_bootstrap()` (lines 296-312)
- `_animated_figure.py` `_generate_fullpage_bootstrap()` (lines 314-330)

**Plan:** `generate_bootstrap_js(adapter_js: str) -> str` in `_bootstrap/_html.py`. All four callers become one-liners.

### 2.4 `_html.py` Uses `export_viewer.html` Template Instead of `html_fullpage_template()`

`_html.py` `render_export_html()` reads a separate template file and does string replacements:

```python
html = (_TEMPLATES_DIR / "export_viewer.html").read_text()
bootstrap = _generate_bootstrap(scene_config)

return (
    html.replace("__SCENE_DATA_JSON__", scene_json)
    .replace("__SCENE_CONFIG_JSON__", config_json)
    .replace("__BOOTSTRAP_JS__", bootstrap)
)
```

Meanwhile, `html_fullpage_template()` in `_bootstrap/_html.py` already produces an identical HTML structure but composes it from parameters.

**Plan:** Check if `export_viewer.html` template can be replaced by `html_fullpage_template()` call. If the template has additional content not covered by the function, extend the function. Otherwise, delete the template and use the function. **Decision deferred** — the template reads data from `<script id="tanga-scene-data">` and `<script id="tanga-scene-config">` elements which `html_fullpage_template()` doesn't currently produce. This is a separate concern.

### 2.5 Unused `js_animation_playback()` in old `_bootstrap_core.py`

A ~100-line function imported by `_animated_figure.py` but never called. The actual playback engine is `_animated_playback_engine()` defined in `_animated_figure.py`.

**Plan:** Delete `js_animation_playback()` from the old `_bootstrap_core.py` (replaced by `js_animated_render_loop()` in `_bootstrap/_animation.py`). The improved version from `_animated_figure.py`'s `_animated_playback_engine()` becomes `js_animated_render_loop()` in `_bootstrap/_animation.py`.

### 2.6 CDN Script Tags Duplicated in `html_fullpage_template()` and `html_snippet_template()`

Both template functions embed identical CDN `<script>` tags for `marked`, `katex`, and `katex/auto-render`. Also the Three.js import map is identical.

**Plan:** Extract shared constants:
- `_CDN_SCRIPTS` — `<script>` tags for marked + KaTeX
- `_THREEJS_IMPORT_MAP` — the importmap block

Use these in both template functions.

---

## 3. File Split: `_bootstrap_core.py` → `_bootstrap/` Package

Current: **1173 lines** — mixing utilities, scene setup, entity/label rendering, overlays, animation engine, HTML templates, and CDN constants.  The file will be **deleted** and its contents redistributed into the `_bootstrap/` package.  Re-exports live in `_bootstrap/__init__.py`.

### 3.1 Proposed Structure

```
py/pytanga/viz/export/
├── _bootstrap_core.py              (DELETED)
├── _bootstrap/
│   ├── __init__.py                 (→ ~45 lines, re-exports facade)
│   ├── _utils.py                   (→ ~30 lines)
│   ├── _scene.py                   (→ ~220 lines)
│   ├── _entities.py                (→ ~210 lines)
│   ├── _overlays.py                (→ ~130 lines)
│   ├── _animation.py               (→ ~470 lines)
│   └── _html.py                    (→ ~170 lines)
```

All three exporter files (`_html.py`, `_figure_html.py`, `_animated_figure.py`) change their imports from `pytanga.viz.export._bootstrap_core` to `pytanga.viz.export._bootstrap`.  The old `_bootstrap_core.py` file is deleted.  The public API (`_bootstrap.xyz`) remains identical — only the import path changes.

### 3.2 Module Contents

#### `_bootstrap/_utils.py` (~30 lines)
- `_escape_html(text)` 
- `_escape_js(s)`
- `_format_js_bool(val)`
- `contains_math(text)`

#### `_bootstrap/_scene.py` (~220 lines)
- `js_imports()` — Three.js imports
- `js_scene_setup(...)` — scene, camera, renderers, controls, lighting, grid, axes
- `js_render_loop(...)` — requestAnimationFrame loop
- `js_resize_handler(...)` — window resize listener
- `js_autofit_camera(...)` — bounding box auto-fit

#### `_bootstrap/_entities.py` (~210 lines)
- `js_entity_creation(...)` — entity mesh creation loop (layer dispatch or simple)
- `js_label_creation(...)` — animated label CSS2D creation (with optional labelObjects Map)
- `js_label_creation_static(...)` — static label CSS2D creation (with offset2d + alignment)

#### `_bootstrap/_overlays.py` (~130 lines)
- `js_title_overlay(...)` — title DOM element
- `js_annotation_panel(...)` — markdown + KaTeX annotation panel
- `js_footer(...)` — footer DOM element

#### `_bootstrap/_animation.py` (~470 lines)
- **JS constants:**
  - `_GET_ANIM_DATA_JS`
  - `_ANIMATION_DECOMPRESS_JS`
  - `_CONTROLS_HTML`
  - `_CONTROLS_JS`
  - `_ANNOTATION_CONTROLS_REPOSITION_JS`
- **JS generator functions:**
  - `js_animated_label_function(label_map_var)` ← **NEW** (replaces `_createLabel`/`_createLabelFull` inline in `_animated_figure.py`)
  - `js_animation_state()` ← **NEW** (replaces duplicated state block)
  - `js_animation_data_init(fps, extra_maps)` ← **NEW** (replaces duplicated data init block)
  - `js_controls_ui(show_controls)` — returns `_CONTROLS_JS` or empty
  - `js_controls_html(show_controls)` — returns `_CONTROLS_HTML` or empty
  - `js_annotation_controls_reposition()` — returns reposition script
  - `js_animated_render_loop(...)` ← **MOVED** from `_animated_figure.py._animated_playback_engine()`, renamed
- **Animation data helpers:**
  - `embed_animation_data(json_str, compress)`
  - `get_anim_decompress_js(compress)`
  - `get_anim_data_js()`

#### `_bootstrap/_html.py` (~170 lines)
- **Constants:**
  - `_CDN_SCRIPTS` ← **NEW** (shared CDN script tags)
  - `_THREEJS_IMPORT_MAP` ← **NEW** (shared import map)
  - `_KATEX_CSS_LINK`
- **Functions:**
  - `katex_css_if_needed(recording_data, fig_config, annotation, footer)`
  - `html_fullpage_template(...)` — full-page document wrapper
  - `html_snippet_template(...)` — snippet wrapper
- **Bootstrap concatenation:**
  - `_RENDERER_FILES` ← **MOVED** from `_figure_html.py` and `_html.py`
  - `_strip_imports(source)` ← **MOVED** from `_figure_html.py` and `_html.py`
  - `generate_bootstrap_js(adapter_js)` ← **NEW** (shared concatenation pattern)

#### `_bootstrap/__init__.py` (→ ~45 lines, facade re-export)
```python
# Re-export everything from submodules
from pytanga.viz.export._bootstrap._utils import (
    _escape_html, _escape_js, _format_js_bool, contains_math,
)
from pytanga.viz.export._bootstrap._scene import (
    js_imports, js_scene_setup, js_render_loop,
    js_resize_handler, js_autofit_camera,
)
from pytanga.viz.export._bootstrap._entities import (
    js_entity_creation, js_label_creation, js_label_creation_static,
)
from pytanga.viz.export._bootstrap._overlays import (
    js_title_overlay, js_annotation_panel, js_footer,
)
from pytanga.viz.export._bootstrap._animation import (
    js_animated_label_function,
    js_animation_state,
    js_animation_data_init,
    js_controls_ui,
    js_controls_html,
    js_annotation_controls_reposition,
    js_animated_render_loop,
    embed_animation_data,
    get_anim_decompress_js,
    get_anim_data_js,
)
from pytanga.viz.export._bootstrap._html import (
    _RENDERER_FILES,
    _strip_imports,
    generate_bootstrap_js,
    katex_css_if_needed,
    html_fullpage_template,
    html_snippet_template,
)
```

All exporter files import from `pytanga.viz.export._bootstrap` instead of the old `_bootstrap_core`.  The old `_bootstrap_core.py` file is deleted.

---

## 4. Implementation Checklist

### 4.1 Create `_bootstrap/` package
- [ ] **S1:** Create `py/pytanga/viz/export/_bootstrap/` directory
- [ ] **S2:** Create `py/pytanga/viz/export/_bootstrap/__init__.py` (empty)

### 4.2 Split `_bootstrap_core.py` into submodules
- [ ] **S3:** Create `_bootstrap/_utils.py` — move utility helpers
- [ ] **S4:** Create `_bootstrap/_scene.py` — move scene/setup JS generators
- [ ] **S5:** Create `_bootstrap/_entities.py` — move entity/label JS generators
- [ ] **S6:** Create `_bootstrap/_overlays.py` — move title/annotation/footer JS generators
- [ ] **S7:** Create `_bootstrap/_animation.py` — move all animation JS constants + generators + data helpers
- [ ] **S8:** Create `_bootstrap/_html.py` — move HTML template helpers + `_RENDERER_FILES` + `_strip_imports` + `generate_bootstrap_js`

### 4.3 Add new shared JS generator functions
- [ ] **N1:** Implement `js_animated_label_function(label_map_var: str = "")` — replaces `_createLabel`/`_createLabelFull` inline code
- [ ] **N2:** Implement `js_animation_state()` — replaces duplicated state variable declarations
- [ ] **N3:** Implement `js_animation_data_init(fps: int, extra_maps: str = "")` — replaces duplicated data init block
- [ ] **N4:** Move `_animated_playback_engine()` from `_animated_figure.py` → `js_animated_render_loop()` in `_bootstrap/_animation.py`; delete existing unused `js_animation_playback()` from `_bootstrap_core.py`
- [ ] **N5:** Implement `generate_bootstrap_js(adapter_js: str) -> str` — shared concatenation pattern

### 4.4 Add shared constants
- [ ] **C1:** Extract `_CDN_SCRIPTS` — shared marked + KaTeX `<script>` tags
- [ ] **C2:** Extract `_THREEJS_IMPORT_MAP` — shared Three.js import map block
- [ ] **C3:** Move `_RENDERER_FILES` to `_bootstrap/_html.py`, import from both `_html.py` and `_figure_html.py`
- [ ] **C4:** Move `_strip_imports()` to `_bootstrap/_html.py`, import from both `_html.py` and `_figure_html.py`

### 4.5 Populate `_bootstrap/__init__.py` with re-exports
- [ ] **F1:** Write re-exports in `_bootstrap/__init__.py` (~45 lines)
- [ ] **F2:** Delete `_bootstrap_core.py` (old 1173-line file)
- [ ] **F3:** Change all importers to import from `pytanga.viz.export._bootstrap` instead of `pytanga.viz.export._bootstrap_core`

### 4.6 Refactor `_animated_figure.py`
- [ ] **A1:** Replace inline `_createLabel` with `js_animated_label_function(label_map_var="")`
- [ ] **A2:** Replace inline `_createLabelFull` with `js_animated_label_function(label_map_var="labelObjects")`
- [ ] **A3:** Replace duplicated animation state block with `js_animation_state()`
- [ ] **A4:** Replace duplicated animation data init block with `js_animation_data_init(fps, extra_maps="\nconst labelObjects = new Map();")` for full-page
- [ ] **A5:** Replace inline resize handler in figure adapter with `js_resize_handler(conditional=True, container_expr="figContainer")`
- [ ] **A6:** Replace inline resize handler in full-page adapter with `js_resize_handler()` (non-conditional)
- [ ] **A7:** Replace inline auto-fit camera in figure adapter with `js_autofit_camera()` call
- [ ] **A8:** Replace `_animated_playback_engine()` call with `js_animated_render_loop()` import
- [ ] **A9:** Delete `_animated_playback_engine()` from `_animated_figure.py`

### 4.7 Refactor `_html.py`
- [ ] **H1:** Change import from `pytanga.viz.export._bootstrap_core` → `pytanga.viz.export._bootstrap`
- [ ] **H2:** Replace `_strip_imports()` definition with import from `_bootstrap`
- [ ] **H3:** Replace `_RENDERER_FILES` definition with import from `_bootstrap`
- [ ] **H4:** Replace `_generate_bootstrap()` body with `generate_bootstrap_js()` call

### 4.8 Refactor `_figure_html.py`
- [ ] **F1:** Change import from `pytanga.viz.export._bootstrap_core` → `pytanga.viz.export._bootstrap`
- [ ] **F2:** Replace `_strip_imports()` definition with import from `_bootstrap`
- [ ] **F3:** Replace `_RENDERER_FILES` definition with import from `_bootstrap`
- [ ] **F4:** Replace `_generate_figure_bootstrap()` body with `generate_bootstrap_js()` call

### 4.9 Refactor `_animated_figure.py` imports
- [ ] **AN1:** Change import from `pytanga.viz.export._bootstrap_core` → `pytanga.viz.export._bootstrap`
- [ ] **AN2:** Update import of `_RENDERER_FILES` from `_figure_html.py` → from `_bootstrap`
- [ ] **AN3:** Update import of `_strip_imports` from `_figure_html.py` → from `_bootstrap`
- [ ] **AN4:** Replace `_generate_animated_bootstrap()` body with `generate_bootstrap_js()` call
- [ ] **AN5:** Replace `_generate_fullpage_bootstrap()` body with `generate_bootstrap_js()` call

### 4.10 Verification
- [ ] **V1:** `uv run python -c "from pytanga.viz.export._bootstrap import *"` succeeds
- [ ] **V2:** `uv run python -c "from pytanga.viz.export._html import render_export_html"` succeeds
- [ ] **V3:** `uv run python -c "from pytanga.viz.export._figure_html import render_export_figure"` succeeds
- [ ] **V4:** `uv run python -c "from pytanga.viz.export._animated_figure import render_export_animated_figure, render_export_animated_html"` succeeds
- [ ] **V5:** Smoke test: static full-page export contains title and annotation
- [ ] **V6:** Smoke test: static figure export contains title, annotation, footer
- [ ] **V7:** Smoke test: animated full-page export contains title
- [ ] **V8:** Smoke test: animated figure export contains title, annotation, footer (bug fix regression)
- [ ] **V9:** All existing tests pass (except pre-existing `test_cache.py` failure)
- [ ] **V10:** Diff generated JS bootstrap of each export path before/after — functionally identical

---

## 5. Line Count Target

| File | Before | After | Delta |
|------|--------|-------|-------|
| `_bootstrap_core.py` | 1173 | 0 (deleted) | -1173 |
| `_bootstrap/__init__.py` (new) | 0 | ~45 | +45 |
| `_bootstrap/_utils.py` (new) | 0 | ~30 | +30 |
| `_bootstrap/_scene.py` (new) | 0 | ~220 | +220 |
| `_bootstrap/_entities.py` (new) | 0 | ~210 | +210 |
| `_bootstrap/_overlays.py` (new) | 0 | ~130 | +130 |
| `_bootstrap/_animation.py` (new) | 0 | ~490 | +490 |
| `_bootstrap/_html.py` (new) | 0 | ~230 | +230 |
| `_html.py` | 357 | ~290 | -67 |
| `_figure_html.py` | 349 | ~280 | -69 |
| `_animated_figure.py` | 798 | ~540 | -258 |
| **Total** | 2677 | ~2465 | **-212** |

Total line count decreases by ~217. More importantly, each file has a clear single responsibility and the `_bootstrap/` submodules can be understood independently.

---

## 6. Files Modified / Created

### New Files
| File | Content |
|------|---------|
| `py/pytanga/viz/export/_bootstrap/__init__.py` | Facade re-export (~45 lines) |
| `py/pytanga/viz/export/_bootstrap/_utils.py` | Escape helpers + `contains_math` |
| `py/pytanga/viz/export/_bootstrap/_scene.py` | Scene/camera/renderer/loop setup |
| `py/pytanga/viz/export/_bootstrap/_entities.py` | Entity + label creation JS |
| `py/pytanga/viz/export/_bootstrap/_overlays.py` | Title/annotation/footer overlays |
| `py/pytanga/viz/export/_bootstrap/_animation.py` | Animation playback engine + controls |
| `py/pytanga/viz/export/_bootstrap/_html.py` | HTML templates + bootstrap concatenation + shared asset lists |

### Modified Files
| File | Changes |
|------|---------|
| `_html.py` | Change imports to `_bootstrap`; use `generate_bootstrap_js()`; remove local `_strip_imports` and `_RENDERER_FILES` |
| `_figure_html.py` | Change imports to `_bootstrap`; use `generate_bootstrap_js()`; remove local `_strip_imports` and `_RENDERER_FILES` |
| `_animated_figure.py` | Change imports to `_bootstrap`; replace all inline JS templates with shared functions; use `generate_bootstrap_js()` |

### Files Deleted
| File | Reason |
|------|--------|
| `_bootstrap_core.py` | Replaced by `_bootstrap/` package; re-exports now live in `_bootstrap/__init__.py` |

### Files NOT Modified
- `_exporter.py` — unchanged (public API)
- All JS renderer modules — unchanged
- `export_viewer.html` template — unchanged (deferred decision)

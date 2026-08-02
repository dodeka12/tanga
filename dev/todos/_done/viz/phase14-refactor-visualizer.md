# Phase 14 — Refactor Visualizer (Extract Exporter + Style Factories)

**Prerequisites:** Phase 13 (figure export), Phase 12 (title/annotation), Phase 11 (HTML/glTF export)

**Goal:** Reduce `visualizer.py` from ~1080 lines to ~480 lines by extracting
export logic into a new `SceneExporter` class, moving default style
initialization + style-resolution helpers to `_style_dict.py`, and moving
`FigureConfig`/`FigureStyle` defaults into `SceneExporter`.  This is a
**breaking change** — export methods are removed from `Visualizer` and
users create a `SceneExporter(viz)` instance to export.

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Current State

`visualizer.py` has grown to ~1080 lines.  The `Visualizer` class alone is
~780 lines with 31 methods across 8 distinct responsibilities:

| Responsibility | Lines | Location |
|---------------|-------|----------|
| `__init__` + default style init | ~130 | Class body |
| Entity management | ~90 | Class body |
| Title & annotation | ~50 | Class body |
| Style config | ~20 | Class body |
| MV resolution | ~20 | Class body |
| Animation | ~40 | Class body |
| Export (HTML, glTF, figure) | ~150 | Class body |
| Server lifecycle | ~100 | Class body |
| Properties | ~90 | Class body |
| Module helpers | ~200 | Module-level |

The file does too much.  Adding future export formats (PDF, SVG, WebM video
capture) would bloat it further.  Export and style logic are conceptually
separate from animation, entity management, and server lifecycle.

### 1.2 Design Goals

1. **Single Responsibility** — `Visualizer` owns the scene, server, entity
   management, and properties.  Export logic moves to `SceneExporter`.

2. **Clean API** — Export is a separate concern.  Users create a
   `SceneExporter(viz)` and call methods on it:
   ```python
   from pytanga.viz import SceneExporter
   exporter = SceneExporter(viz)
   exporter.export_html("scene.html")
   exporter.export_figure("figure.html", style=FigureStyle(auto_rotate=True))
   ```

3. **Factory functions for default styles** — The four style initialization
   blocks in `Visualizer.__init__` become standalone factory functions
   in `_style_dict.py`.

4. **Style-resolution helpers move** — `_resolve_label_style`,
   `_resolve_annotation_style`, `_resolve_figure_style`, and `_kind_to_key`
   move to `_style_dict.py` where they logically belong.

5. **`FigureConfig` and `FigureStyle` defaults move to `SceneExporter`** —
   `_default_figure_style` and `figure_config` are not needed by
   `Visualizer` (it doesn't export anything anymore).  They live on
   `SceneExporter` as `default_figure_style` and `figure_config` properties.

6. **No circular imports** — `SceneExporter` lives in
   `py/pytanga/viz/export/_exporter.py`.  It imports from `Visualizer`
   (type annotation only), not the other way around.

---

## 2. New Class: `SceneExporter`

### 2.1 Location

`py/pytanga/viz/export/_exporter.py` (new file)

### 2.2 Design

```python
# py/pytanga/viz/export/_exporter.py

from __future__ import annotations

import json
import tempfile
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytanga.viz.visualizer import Visualizer

from pytanga.viz._figure import FigureConfig
from pytanga.viz._styles import FigureStyle as _FS


class SceneExporter:
    """Exports a Visualizer's scene to HTML, glTF, or presentation figures.

    Usage::

        from pytanga.viz import SceneExporter

        exporter = SceneExporter(viz)
        exporter.export_html("scene.html")
        exporter.export_figure("figure.html", style=FigureStyle(width=1024))
        exporter.open_figure()
    """

    def __init__(self, visualizer: Visualizer) -> None:
        self._viz = visualizer
        self._default_figure_style = _FS(
            width=800, height=600, background="transparent",
            auto_rotate=False, show_grid=True, show_axes=True,
            show_title=True, show_annotation=True, border_radius="0",
        )
        self._figure_config: FigureConfig | None = None

    # ── Properties ──────────────────────────────────────

    @property
    def default_figure_style(self) -> FigureStyle:
        """Mutable canonical ``FigureStyle`` for this exporter."""
        return self._default_figure_style

    @property
    def figure_config(self) -> FigureConfig:
        """Lazy-initialized ``FigureConfig``, inherits from visualizer."""
        if self._figure_config is None:
            self._figure_config = FigureConfig(
                title=self._viz._title,
                annotation=self._viz._annotation,
                footer=self._viz._annotation,
            )
        return self._figure_config

    # ── Path resolution ────────────────────────────────

    @staticmethod
    def _resolve_export_path(path: str | Path, extension: str) -> Path:
        """Resolve *path*, adding *extension* if missing."""
        ...

    # ── HTML / glTF ────────────────────────────────────

    def export_html(self, path: str | Path, *, overwrite=False) -> None:
        """Export as self-contained HTML file."""
        ...

    def export_glb(self, path: str | Path, *, overwrite=False) -> None:
        """Export as glTF 2.0 binary (``.glb``)."""
        ...

    # ── Figure ─────────────────────────────────────────

    def export_figure(self, path: str | Path, *, style=None,
                      overwrite=False) -> None:
        """Export as presentation-ready HTML snippet."""
        ...

    def export_figure_html(self, *, style=None) -> str:
        """Return figure export as HTML snippet string."""
        ...

    def open_figure(self, *, style=None) -> None:
        """Open standalone browser window at figure dimensions."""
        ...
```

### 2.3 Internal Access

`SceneExporter` accesses `Visualizer` internals via `self._viz`:

- `self._viz._scene` — the `Scene` instance
- `self._viz._config` — the `SceneConfig` instance
- `self._viz._default_styles` — per-kind entity styles
- `self._viz._title` — viewport title
- `self._viz._annotation` — markdown annotation text

These are the same private attributes the export methods currently access
directly inside `Visualizer`.  No new public API surface is needed.

### 2.4 What Is Removed from `Visualizer`

| Method | Fate |
|--------|------|
| `export_html()` | Removed |
| `export_glb()` | Removed |
| `export_figure()` | Removed |
| `export_figure_html()` | Removed |
| `open_figure()` | Removed |
| `_resolve_export_path()` | Removed |
| `figure_config` property | Removed |
| `default_figure_style` property | Removed |
| `_default_figure_style` attribute in `__init__` | Removed |

Methods that **stay** on `Visualizer`:
- `add`, `update`, `update_entity`, `update_label`, `remove`, `clear`
- `set_title`, `set_annotation`, `_push_scene_config`, `sleep_ms`
- `set_default_color`, `_resolve`
- `animate_to`, `timeline`, `_send_raw`
- `start`, `stop`, `flush`, `run`, `_flush_async`
- `_repr_html_`, all remaining properties

---

## 3. Default Style Factory Functions

### 3.1 Move to `_style_dict.py`

Four new factory functions in `py/pytanga/viz/_style_dict.py`:

```python
def _make_default_label_style() -> LabelStyle:
    return LabelStyle(
        font_size=14, font_family="sans-serif", color="#ffffff",
        background="rgba(0, 0, 0, 0.6)",
        offset_local=(0.0, 0.0, 0.0), offset_2d=(0.0, 0.0),
        align=(0.5, 0.5),
    )

def _make_default_annotation_style() -> AnnotationStyle:
    return AnnotationStyle(
        width="100%", max_width="800px", max_height="250px",
        font_size=13, font_family="sans-serif", color="#cccccc",
        background="rgba(0, 0, 0, 0.75)", link_color="#88ccff",
        code_background="rgba(255, 255, 255, 0.1)",
        padding="10px 16px", border_radius="4px",
    )

def _make_default_label_styles() -> dict[str, LabelStyle | None]:
    return {
        "Point": None, "Direction": None, "HPoint": None,
        "PointPair": None, "Line": None, "Plane": None,
        "Circle": None, "Sphere": None, "Space": None,
        "ReflectionLine": None, "ReflectionPlane": None,
        "ReflectionOrigin": None, "Inversion": None,
        "Rotor": None, "Translator": None, "Dilator": None,
        "Motor": None, "GeneralRotor": None, "GeneralDilator": None,
    }
```

Note: `_make_default_figure_style()` is **not** in `_style_dict.py` —
it lives on `SceneExporter.__init__` since the figure style is
export-specific.

### 3.2 Impact on `Visualizer.__init__`

```python
# Before (~40 lines of inline style init)
# After (3 lines):
from ._style_dict import (
    _make_default_label_style, _make_default_annotation_style,
    _make_default_label_styles,
)
self._default_label_style = _make_default_label_style()
self._default_annotation_style = _make_default_annotation_style()
self._default_label_styles = _make_default_label_styles()
```

---

## 4. Move Style-Resolution Helpers

### 4.1 Functions to Move

| Function | From | To |
|----------|------|----|
| `_kind_to_key` | `visualizer.py` | `_style_dict.py` |
| `_resolve_label_style` | `visualizer.py` | `_style_dict.py` |
| `_resolve_annotation_style` | `visualizer.py` | `_style_dict.py` |
| `_resolve_figure_style` | `visualizer.py` | `_style_dict.py` |

### 4.2 Impact on `visualizer.py`

`Visualizer.set_annotation()` and `Visualizer.add()` update their imports:

```python
# Before:
style_dict = _resolve_annotation_style(self._default_annotation_style, style)

# After:
from ._style_dict import _resolve_annotation_style
style_dict = _resolve_annotation_style(self._default_annotation_style, style)
```

---

## 5. Migration of Test/Dev Scripts

Existing scripts using `viz.export_html(...)`, `viz.export_figure(...)`,
`viz.open_figure(...)` must be updated:

```python
# Before:
viz.export_html("test.html", overwrite=True)
viz.export_figure("figure.html", style=FigureStyle(width=800))
viz.open_figure()

# After:
from pytanga.viz import SceneExporter
exporter = SceneExporter(viz)
exporter.export_html("test.html", overwrite=True)
exporter.export_figure("figure.html", style=FigureStyle(width=800))
exporter.open_figure()
```

Scripts to update:
- `dev/src/test_viz_smoke.py` — `viz.export_html(...)` → `SceneExporter(viz).export_html(...)`
- `dev/src/test_viz_play.py` — `viz.export_html(...)` → `SceneExporter(viz).export_html(...)`
- `dev/src/test_viz_figure.py` — `viz.export_figure(...)` → `exporter.export_figure(...)`
- `dev/src/test_viz_notebook.ipynb` — same pattern
- `dev/src/test_export_smoke.py` — may need `SceneExporter` import

---

## 6. Files to Create / Modify

### 6.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/export/_exporter.py` | `SceneExporter` class: `__init__`, `default_figure_style` property, `figure_config` property, `_resolve_export_path`, `export_html`, `export_glb`, `export_figure`, `export_figure_html`, `open_figure` |

### 6.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/_style_dict.py` | Add `_make_default_label_style`, `_make_default_annotation_style`, `_make_default_label_styles` factory functions.  Add `_kind_to_key`, `_resolve_label_style`, `_resolve_annotation_style`, `_resolve_figure_style` (moved from `visualizer.py`). |
| `py/pytanga/viz/visualizer.py` | Replace inline style init with factory function calls.  Remove all export/figure methods.  Remove `figure_config`/`default_figure_style` properties.  Remove `_resolve_export_path`, `_resolve_figure_style`, `_kind_to_key`, `_resolve_label_style`, `_resolve_annotation_style` (moved).  Update internal imports. |
| `py/pytanga/viz/__init__.py` | Export `SceneExporter` from `_exporter.py`.  Remove `FigureConfig`/`FigureStyle` from exports (user imports from `pytanga.viz` should include `FigureConfig`/`FigureStyle` only if they want them for type hints — they can still import them). |
| `dev/src/test_viz_smoke.py` | Replace `viz.export_html(...)` with `SceneExporter(viz).export_html(...)` |
| `dev/src/test_viz_play.py` | Replace `viz.export_html(...)` with `SceneExporter(viz).export_html(...)` |
| `dev/src/test_viz_figure.py` | Replace `viz.export_figure(...)`/`viz.open_figure()` with `SceneExporter(viz).export_figure(...)`/`SceneExporter(viz).open_figure()` |
| `dev/src/test_viz_notebook.ipynb` | Same pattern (if it uses export) |
| `dev/src/test_export_smoke.py` | Import `SceneExporter`, update call sites |

### 6.3 Files NOT Modified

- `py/pytanga/viz/export/_html.py` — unchanged
- `py/pytanga/viz/export/_gltf.py` — unchanged
- `py/pytanga/viz/export/_figure_html.py` — unchanged
- `py/pytanga/viz/scene.py` — unchanged
- `py/pytanga/viz/serializer.py` — unchanged
- `py/pytanga/viz/server.py` — unchanged
- `py/pytanga/viz/_styles.py` — unchanged (FigureStyle stays, AnnotationStyle stays)
- `py/pytanga/viz/_figure.py` — unchanged (FigureConfig stays)
- `py/pytanga/viz/_label.py` — unchanged
- `py/pytanga/viz/_props.py` — unchanged
- `py/pytanga/viz/_timeline.py` — unchanged
- `py/pytanga/viz/_types.py` — unchanged
- All JS files — unchanged

---

## 7. Implementation Checklist

### 7.1 `_style_dict.py` — Factory Functions

- [ ] **S1:** Add `_make_default_label_style() -> LabelStyle` factory function
- [ ] **S2:** Add `_make_default_annotation_style() -> AnnotationStyle` factory function
- [ ] **S3:** Add `_make_default_label_styles() -> dict[str, LabelStyle | None]` factory function
- [ ] **S4:** Verify all three functions produce identical results to the current inline code

### 7.2 `_style_dict.py` — Moved Helpers

- [ ] **S5:** Move `_kind_to_key` from `visualizer.py` to `_style_dict.py`
- [ ] **S6:** Move `_resolve_label_style` from `visualizer.py` to `_style_dict.py`
- [ ] **S7:** Move `_resolve_annotation_style` from `visualizer.py` to `_style_dict.py`
- [ ] **S8:** Move `_resolve_figure_style` from `visualizer.py` to `_style_dict.py`
- [ ] **S9:** Update `visualizer.py` imports: `from ._style_dict import _kind_to_key, _resolve_label_style, _resolve_annotation_style`

### 7.3 `_exporter.py` — New SceneExporter Class

- [ ] **E1:** Create `py/pytanga/viz/export/_exporter.py`
- [ ] **E2:** Define `SceneExporter.__init__(self, visualizer: Visualizer)` storing `self._viz`
- [ ] **E3:** Initialize `self._default_figure_style` with canonical `FigureStyle` (moved from `Visualizer.__init__`)
- [ ] **E4:** Add `default_figure_style` property returning `self._default_figure_style`
- [ ] **E5:** Add `figure_config` property (lazy-init `FigureConfig` inheriting from `self._viz._title` / `self._viz._annotation`)
- [ ] **E6:** Move `_resolve_export_path` static method from `visualizer.py` to `SceneExporter`
- [ ] **E7:** Move `export_html` method logic from `Visualizer` to `SceneExporter` (accessing `self._viz._scene`, `self._viz._config`, etc.)
- [ ] **E8:** Move `export_glb` method logic from `Visualizer` to `SceneExporter`
- [ ] **E9:** Move `export_figure` method logic from `Visualizer` to `SceneExporter`
- [ ] **E10:** Move `export_figure_html` method logic from `Visualizer` to `SceneExporter`
- [ ] **E11:** Move `open_figure` method logic from `Visualizer` to `SceneExporter`
- [ ] **E12:** No imports from `visualizer.py` at runtime (TYPE_CHECKING only for annotation)

### 7.4 `visualizer.py` — Clean Up

- [ ] **V1:** Replace inline `_default_label_style = _LS(...)` with `_make_default_label_style()`
- [ ] **V2:** Replace inline `_default_annotation_style = _AS(...)` with `_make_default_annotation_style()`
- [ ] **V3:** Remove `_default_figure_style = _FS(...)` block (moved to `SceneExporter`)
- [ ] **V4:** Replace inline `_default_label_styles = { ... }` with `_make_default_label_styles()`
- [ ] **V5:** Remove `export_html` method
- [ ] **V6:** Remove `export_glb` method
- [ ] **V7:** Remove `export_figure` method
- [ ] **V8:** Remove `export_figure_html` method
- [ ] **V9:** Remove `open_figure` method
- [ ] **V10:** Remove `_resolve_export_path` method
- [ ] **V11:** Remove `figure_config` property (moved to `SceneExporter`)
- [ ] **V12:** Remove `default_figure_style` property (moved to `SceneExporter`)
- [ ] **V13:** Remove `_resolve_figure_style` function (moved to `_style_dict.py`)
- [ ] **V14:** Remove `_kind_to_key` function (moved to `_style_dict.py`)
- [ ] **V15:** Remove `_resolve_label_style` function (moved to `_style_dict.py`)
- [ ] **V16:** Remove `_resolve_annotation_style` function (moved to `_style_dict.py`)
- [ ] **V17:** Update internal imports in `set_annotation()` and `add()` to import from `_style_dict`
- [ ] **V18:** `visualizer.py` should be <500 lines

### 7.5 `__init__.py`

- [ ] **I1:** Import and export `SceneExporter` from `py/pytanga/viz/export/_exporter`

### 7.6 Test/Dev Script Updates

- [ ] **T1:** `dev/src/test_viz_smoke.py` — replace `viz.export_html(...)` with `SceneExporter(viz).export_html(...)`
- [ ] **T2:** `dev/src/test_viz_play.py` — replace `viz.export_html(...)` with `SceneExporter(viz).export_html(...)`
- [ ] **T3:** `dev/src/test_viz_figure.py` — replace `viz.export_figure(...)`/`viz.open_figure()` with `SceneExporter(viz).export_figure(...)`/`SceneExporter(viz).open_figure()`
- [ ] **T4:** `dev/src/test_export_smoke.py` — update imports and call sites if needed

### 7.7 Verification

- [ ] **V1:** `from pytanga.viz import Visualizer, SceneExporter` works without errors
- [ ] **V2:** `exporter = SceneExporter(viz)` works
- [ ] **V3:** `exporter.export_html("test.html", overwrite=True)` produces valid HTML (same as before)
- [ ] **V4:** `exporter.export_figure("figure.html", overwrite=True)` produces valid snippet (same as before)
- [ ] **V5:** `exporter.export_figure_html()` returns valid snippet string (same as before)
- [ ] **V6:** `exporter.export_glb("test.glb", overwrite=True)` produces valid glTF (same as before)
- [ ] **V7:** `exporter.default_figure_style.width` is mutable and affects next export
- [ ] **V8:** `exporter.figure_config.footer` auto-inherits from `viz._annotation`
- [ ] **V9:** `_make_default_label_style()` produces identical result to old inline code
- [ ] **V10:** `_make_default_annotation_style()` produces identical result to old inline code
- [ ] **V11:** `_make_default_label_styles()` produces identical dict to old inline code
- [ ] **V12:** `_kind_to_key("point")` returns `"Point"` (moved, still works)
- [ ] **V13:** All 97 existing tests pass after updating test scripts
- [ ] **V14:** No circular imports
- [ ] **V15:** `hasattr(viz, "export_html")` is `False`

### 7.8 Smoke / Manual

- [ ] **M1:** Run `dev/src/test_viz_smoke.py` — all entity types render
- [ ] **M2:** Run `dev/src/test_viz_figure.py` — figure export produces correct output
- [ ] **M3:** Run `dev/src/test_viz_play.py` — live viewer works end-to-end
- [ ] **M4:** Browser console has no errors in live viewer

---

## 8. Summary of API Changes

| Old API | New API |
|---------|---------|
| `viz.export_html("file.html")` | `SceneExporter(viz).export_html("file.html")` |
| `viz.export_glb("file.glb")` | `SceneExporter(viz).export_glb("file.glb")` |
| `viz.export_figure("file.html")` | `SceneExporter(viz).export_figure("file.html")` |
| `viz.export_figure_html()` | `SceneExporter(viz).export_figure_html()` |
| `viz.open_figure()` | `SceneExporter(viz).open_figure()` |
| `viz.figure_config` | `SceneExporter(viz).figure_config` |
| `viz.default_figure_style` | `SceneExporter(viz).default_figure_style` |

---

## 9. Line Count Summary

| File | Before | After | Delta |
|------|--------|-------|-------|
| `visualizer.py` | ~1080 | ~480 | -600 |
| `_exporter.py` (new) | 0 | ~200 | +200 |
| `_style_dict.py` | ~80 | ~220 | +140 |
| **Total** | ~1160 | ~900 | **-260** |

Net reduction of ~260 lines.  The `Visualizer` class goes from ~780 to
~420 lines — nearly half its previous size.

---

## 10. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **11** | `export_html` / `export_glb` move into `SceneExporter` — implementation unchanged, just relocated |
| **13** | `export_figure` / `export_figure_html` / `open_figure` / `figure_config` / `default_figure_style` move into `SceneExporter` — same logic, new home |
| **12** | `set_title`/`set_annotation` stay on `Visualizer` (they modify live state, not export). `SceneExporter` reads the annotation text from the visualizer for footer auto-inheritance. |
| **Test scripts** | All scripts using `viz.export_*` must be updated to `SceneExporter(viz).export_*` |
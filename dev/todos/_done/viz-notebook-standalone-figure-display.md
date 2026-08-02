# Jupyter Notebook Standalone Figure Display — Implementation Plan

**Date:** 1 August 2026
**Status:** Implemented — 1 August 2026
**Approach:** Option B — Add `display_static()` to `Visualizer`

---

## Motivation

The `Visualizer` is the main entry point for 3D scenes — it handles MV analysis
via `_resolve()`, has a rich `add()` API (color, opacity, size, labels), and
users already know it.  But its Jupyter integration (`_repr_html_()`) needs a
**live WebSocket server** running in a daemon thread — heavy for simple static
visualizations, and incompatible with `nbconvert` (notebook → HTML/PDF).

We want a lightweight, **serverless** path: render the current scene as
self-contained Three.js HTML — no ports, no WebSocket, no daemon threads.

The building blocks already exist:
- `Visualizer._build_standalone_html()` already calls `render_export_html()` with
  all the right data (entities, labels, scene config, figure config, figure style).
- `Visualizer` stores entities via `self._scene: Scene`, styles via
  `self._default_styles`, and config via `self._config: SceneConfig`.
- The `render_export_html()` function in `export/_html.py` generates a complete
  standalone HTML document.

We just need to expose a `display_static()` method on `Visualizer` that uses
this existing pipeline.

---

## Design Decisions

### 1. `display_static()` on `Visualizer` (not a new class)

No new `TangaFigure` class.  The `Visualizer` already owns all the data.
`display_static()` snapshots the current scene state and renders it as
standalone HTML using the existing export pipeline.

Dual behaviour:
- **In Jupyter:** returns `IPython.display.HTML` for inline rendering
- **Outside Jupyter:** writes a temp HTML file and opens it in the browser

### 2. Data flow

```
Visualizer.display_static()
  → self._scene.entities  (list[SceneEntity])
  → self._scene.labels    (list[Label])
  → self._config          (SceneConfig)
  → FigureStyle.from_scene_config() or shared defaults
  → FigureConfig           (from self._config fields)
  → render_export_html()   (existing, in export/_html.py)
  → complete HTML string
```

The render already inlines Three.js, entities, labels, lighting, camera, and
resize handling.

### 3. Three.js inline (not CDN)

`render_export_html()` uses CDN imports.  This is fine for notebooks — no
change needed to the export pipeline.

---

## Files to Modify

| File | Change |
|---|---|
| `py/pytanga/viz/visualizer.py` | Add `display_static()` method to `Visualizer` |

That's it — one file, one method.

---

## Detailed Steps

### Step 1 — Add `display_static()` to `Visualizer`

Add to the `Visualizer` class (near the existing `export_html` / `_repr_html_`
methods, around line 626):

```python
def display_static(
    self,
    width: int | str = "100%",
    height: int | str = "500px",
) -> "IPython.display.HTML | None":  # type: ignore[name-defined]
    """Display the current scene as standalone HTML (no server required).

    Unlike :meth:`_repr_html_` which requires a running WebSocket server,
    this method generates a completely self-contained HTML document that
    can be displayed inline in Jupyter notebooks or opened in a browser.

    In a Jupyter notebook, returns an ``IPython.display.HTML`` object
    for inline rendering.  Outside Jupyter, writes a temporary HTML file
    and opens it in the default browser.

    Parameters
    ----------
    width : int | str
        CSS width of the viewer (e.g. ``"100%"`` or ``800``).
    height : int | str
        CSS height of the viewer (e.g. ``"500px"`` or ``600``).

    Returns
    -------
    IPython.display.HTML | None
        An HTML display object in Jupyter, or ``None`` when opening a
        browser tab outside Jupyter.

    Example
    -------
    >>> viz = Visualizer()
    >>> viz.add(Point(1, 2, 3), color="#ff4444")
    >>> viz.add(Sphere(0, 0, 0, 2), opacity=0.3)
    >>> viz.display_static()   # renders inline in Jupyter
    """
    from pytanga.viz.export._html import render_export_html

    _fig_style = self._figure_style if hasattr(self, "_figure_style") else {}
    _fig_config = self._figure_config if hasattr(self, "_figure_config") else {}

    html = render_export_html(
        entities=list(self._scene._entities.values()),
        labels=(
            self._scene._labels
            if hasattr(self._scene, "_labels")
            else None
        ),
        scene_config=self._config.to_dict(),
        figure_config=_fig_config.to_dict(),
        figure_style=_fig_style.to_dict(),
    )

    if self._jupyter:
        from IPython.display import HTML

        return HTML(html)
    else:
        import tempfile
        import webbrowser
        from pathlib import Path

        tmp = Path(tempfile.mktemp(suffix=".html"))
        tmp.write_text(html, encoding="utf-8")
        webbrowser.open(str(tmp))
        return None
```

### Step 2 — Verify entity data access

The `render_export_html()` in `export/_html.py` expects:
- `entities: List[Dict[str, Any]]` — serialized entity dicts (already have `kind`, `data`, `style`)
- `labels: List[Dict[str, Any]]` — serialized label dicts
- `scene_config: Dict[str, Any]` — from `SceneConfig.to_dict()`
- `figure_config: Dict[str, Any]` — from `FigureConfig.to_dict()`
- `figure_style: Dict[str, Any]` — from `FigureStyle.to_dict()`

The `Visualizer._build_standalone_html()` (line 450-463) already calls this
function with the right arguments.  We need to verify that `self._scene._entities`
is a dict (from `Scene.__init__`) and that `self._figure_style` /
`self._figure_config` exist (added in a later version of Visualizer).

If `_figure_style` / `_figure_config` don't exist on the current `Visualizer`,
use `FigureStyle()` and `FigureConfig()` defaults:

```python
_fig_style = getattr(self, "_figure_style", FigureStyle())
_fig_config = getattr(self, "_figure_config", FigureConfig())
```

---

## Notebook Workflow (end-to-end)

```python
# Cell 1: Build up scene with the Visualizer
from pytanga.viz import Visualizer
from pytanga.geometry.sac import Point, Sphere

viz = Visualizer()
viz.add(some_multivector)             # MV analysis via _resolve()
viz.add(Point(1, 2, 3), color="red")
viz.add(Sphere(0, 0, 0, 2), opacity=0.3)

# Cell 2: Display static snapshot
viz.display_static()                  # renders inline
```

Or building a sequence of figures with progressively more entities:

```python
viz = Visualizer()
viz.add(Point(0, 0, 0), color="red")
viz.display_static()                  # Figure 1: just a point

viz.add(Sphere(1, 0, 0, 0.5), color="blue", opacity=0.5)
viz.display_static()                  # Figure 2: point + sphere

viz.add(Line(Point(0,0,0), Direction(0,0,1)), color="green")
viz.display_static()                  # Figure 3: point + sphere + line
```

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| No entities added yet | Renders empty Three.js scene with lighting and background |
| Multiple `display_static()` calls | Each call snapshots current state — independent renders |
| In Jupyter | Returns `IPython.display.HTML` — no browser tab opened |
| Outside Jupyter | Writes temp HTML file, opens in browser — returns `None` |
| `nbconvert` (notebook → HTML/PDF) | `display_static()` is called during execution; HTML embedded in output |
| After `viz.start()` (live server running) | Still works — `display_static()` is independent of the server |
| Pyodide / WASM kernel | Returns `HTML` object (works); non-Jupyter fallback writes temp file (may fail — acceptable) |

---

## Files NOT Requiring Changes

- **`py/pytanga/viz/export/_html.py`**: `render_export_html()` already works.
- **`py/pytanga/viz/_figure.py`**: `FigureConfig` is fine as-is (no new class).
- **`py/pytanga/viz/__init__.py`**: No new exports needed.
- **Frontend/JS**: No changes — HTML generated by the export pipeline works standalone.
- **`py/pytanga/viz/visualizer.py` `_repr_html_()`**: Left unchanged — still uses live iframe when server is running.
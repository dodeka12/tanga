# Phase 8: Integration, Polish & End-to-End Wiring

**Files:** `py/pytanga/viz/__init__.py`, `pyproject.toml`, updates to `visualizer.py` and `server.py`

**Goal:** Wire everything together into a cohesive, importable Python package. Add error
handling, port conflict detection, graceful shutdown, and an `add_mv()` method for
direct multivector visualization via `pytanga.geometry.analyze()`.

**Prerequisites:** All Phases 1–6 (all components exist but may not be wired together)

---

## 1. `__init__.py` — Public API

```python
# py/pytanga/viz/__init__.py

"""Interactive 3D visualization of geometric entities via Three.js.

Provides a zero-dependency (on the browser side) WebSocket + Three.js
pipeline for visualizing pytanga.geometry entities in a web browser.

Usage:
    from pytanga.viz import Visualizer, CameraConfig
    from pytanga.geometry import Point, Sphere

    # Auto-fit camera from entities
    viz = Visualizer()
    viz.add(Point(1, 2, 3), color="#ff4444")
    viz.run()  # opens browser, blocks until Ctrl+C

    # Explicit camera settings
    viz = Visualizer(
        camera=CameraConfig(position=(10, 6, 12), target=(0, 0, 0), fov=50),
        space_extent=15,
    )
    viz.run()
"""

from .visualizer import Visualizer, Timeline
from .scene import CameraConfig, SceneConfig

__all__ = [
    "CameraConfig",
    "SceneConfig",
    "Visualizer",
    "Timeline",
]
```

---

## 2. `pyproject.toml` — Dependency

Add `aiohttp` to the project dependencies:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "aiohttp>=3.9",
]
```

No other changes — Three.js is CDN-loaded, no Python visualization packages needed.

---

## 3. Error Handling & Robustness

### 3.1 Port Conflict Detection

```python
# In server.py — VizServer.start()

async def start(self, flush_callback: FlushCallback) -> None:
    self._flush_callback = flush_callback
    self._app = self._build_app()
    self._runner = web.AppRunner(self._app)
    await self._runner.setup()

    try:
        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()
    except OSError as e:
        if e.errno == 98 or "address already in use" in str(e).lower():
            raise RuntimeError(
                f"Port {self._port} is already in use. "
                f"Close the other process or use Visualizer(port=...) to choose a different port."
            ) from e
        raise
```

### 3.2 Graceful Shutdown on SIGINT

```python
# In visualizer.py — run() method

def run(self) -> None:
    import asyncio
    import signal

    self._server = VizServer(host=self._host, port=self._port)

    async def _run():
        await self._server.start(lambda: self._scene.full_state())
        if self._open_browser:
            self._server.open_browser()
        await self._flush_async()

        # Wait indefinitely until cancelled
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def _signal_handler():
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _signal_handler)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass

        await stop_event.wait()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass
    finally:
        if self._server is not None:
            try:
                asyncio.run(self._server.stop())
            except Exception:
                pass
        print("Visualizer shut down.")
```

### 3.3 Browser Auto-Open with Fallback

```python
# In server.py

def open_browser(self) -> None:
    """Open the viewer URL in the default browser, with graceful fallback."""
    try:
        webbrowser.open(self.url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print(f"Open {self.url} manually to view the scene.")
```

---

## 4. `add()` with Multivectors — Direct MV Visualization

`add()` (defined in Phase 1) accepts both `pytanga.geometry` Entity objects and
`pytanga.MV` (multivector) objects transparently. When an MV is passed, the internal
`_resolve()` method calls `pytanga.geometry.analyze()` to extract the geometric entity
before adding it to the scene. The same applies to `update_entity()`.

```python
from pytanga.algebra import Algebra
from pytanga.viz import Visualizer

pga = Algebra.from_name("PGA3")
viz = Visualizer()

# Create multivectors using the algebra's factory methods
mv_plane = pga.plane(0, 0, 1, 3)      # Plane at z=3
mv_point_opns = pga.point(5, 0, 0)     # Point in OPNS form
mv_point_ipns = pga.point(5, 0, 0)     # Same MV, interpreted as IPNS

# add() handles both Entity and MV objects transparently.
# The 'opns' flag controls how the MV is analyzed.
viz.add(mv_plane, opacity=0.3)                    # MV → analyze(opns=True) → Plane
viz.add(mv_point_opns, color="#ff4444")           # MV → analyze(opns=True) → Point
viz.add(mv_point_ipns, color="#44ff44", opns=False)  # MV → analyze(opns=False) → Point

# Also works with geometry entities directly (opns flag is ignored)
from pytanga.geometry import Sphere, Point
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True)

viz.run()
```

The `_resolve()` logic (from Phase 1):
```python
def _resolve(self, obj, *, opns=True):
    from pytanga.geometry.entities import Entity as GeoEntityType
    if isinstance(obj, GeoEntityType):
        return obj                                # Already an entity
    from pytanga.geometry import analyze
    return analyze(obj, opns=opns)                # MV → analyze → entity
```

---

## 5. Jupyter Notebook Support

The visualizer works in Jupyter notebooks using the **non-blocking mode**
(`start()` + `flush()`) and optionally displaying the viewer in an `<iframe>`.

### 5.1 Auto-Detection of Jupyter

The `Visualizer.__init__` detects the Jupyter environment and adapts:

```python
import sys

def _is_jupyter() -> bool:
    """Detect whether we are running inside a Jupyter notebook/IPython."""
    try:
        from IPython import get_ipython
        shell = get_ipython()
        return shell is not None and hasattr(shell, 'kernel')
    except ImportError:
        return False


class Visualizer:
    def __init__(self, *, open_browser=None, ...):
        # In Jupyter, disable browser open by default (we show an iframe instead)
        if open_browser is None:
            open_browser = not _is_jupyter()
        self._jupyter = _is_jupyter()
        ...
```

### 5.2 IFrame Embedding (`_repr_html_`)

The `Visualizer` supports Jupyter's rich display protocol via `_repr_html_()`.
When the object is the last expression in a notebook cell, Jupyter renders the
viewer inline:

```python
def _repr_html_(self) -> str:
    """Return an HTML iframe embedding the viewer. Used by Jupyter.

    Returns an empty string if the server is not running.
    """
    if self._server is None:
        return "<p style='color:#888'>Visualizer not started. Call <code>.start()</code> first.</p>"

    # Determine viewer height from scene extent (rough heuristic)
    height = 500
    return (
        f'<iframe src="{self.url}" width="100%" height="{height}px" '
        f'style="border: 1px solid #444; border-radius: 4px;" '
        f'title="Tanga 3D Viewer"></iframe>'
    )
```

### 5.3 Typical Notebook Usage

```python
# Cell 1: Setup
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere, Plane, Direction

viz = Visualizer()
viz.start()  # starts server in background thread (non-blocking)
```
```
# Cell 2: Add entities
viz.add(Point(1, 2, 3), color="#ff4444", label="P₁")
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)
viz.add(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.3)
viz.flush()
```
```
# Cell 3: Display the viewer inline
viz  # triggers _repr_html_() — shows iframe
```
```
# Cell 4: Add more later
viz.add(Point(5, 0, 0), color="#44ff44", label="P₂")
viz.flush()  # viewer updates live — no page reload needed
```
```
# Cell 5: Cleanup
viz.stop()
```

### 5.4 Important Notes

- **`run()` must NOT be used** in Jupyter — it blocks the kernel indefinitely.
  Use `start()` / `flush()` / `stop()` instead.
- **The server runs on a background daemon thread.** It survives across notebook
  cells until `stop()` is called or the kernel restarts.
- **The iframe connects via `localhost:8765`.** This works because the browser
  and kernel share the same machine. For remote Jupyter (e.g., Colab, Binder),
  the iframe won't reach `localhost` — users should open the printed URL in a
  separate browser tab instead.
- **`open_browser` defaults to `False`** when Jupyter is detected, so the
  `webbrowser.open()` call is skipped.
- **Port conflicts:** if port 8765 is taken, the `RuntimeError` message appears
  in the notebook output. The user can pass `port=...` to choose another port.

---

## 6. Camera Configuration & Auto-Fit (Consolidated)

The `CameraConfig` dataclass (Phase 1) and `scene_config` WebSocket message
(Phase 3/4) together provide the full camera customization pipeline. Phase 7
ensures this is wired end-to-end:

### 5.1 Python API (already defined in Phase 1)

```python
from pytanga.viz import Visualizer, CameraConfig

# Auto-fit (default)
viz = Visualizer()

# Full explicit
viz = Visualizer(
    camera=CameraConfig(
        position=(10, 6, 12),
        target=(0, 0, 0),
        fov=45,
        near=0.1,
        far=200,
    ),
    space_extent=20,
)

# Partial explicit — position only, auto-compute target and FOV
viz = Visualizer(
    camera=CameraConfig(position=(5, 10, 5)),
)
```

### 5.2 JS Auto-Fit Logic (Phase 4)

`fitCameraToScene()` in `viewer.js` respects explicit settings: if `camera.position`
or `camera.target` is set in `scene_config`, those values are used directly.
Only unspecified fields are auto-computed from the entity bounding box.

### 5.3 Integration Check

- [x] `CameraConfig.to_dict()` → `{ "position": [10,6,12], "fov": 45, ... }`
- [x] `SceneConfig.to_dict()` → `{ "type": "scene_config", "camera": {...}, ... }`
- [x] Server sends `scene_config` before first `scene_update` on connect
- [x] JS applies explicit camera settings; auto-fits for unspecified fields
- [x] `space_extent` controls grid size and default entity extents

---

### 7.1 Package Wiring

- [x] **I1:** Verify `py/pytanga/viz/__init__.py` exports `Visualizer`, `CameraConfig`, `SceneConfig`, `Timeline`, `ObjVizProps`, `VizInputType`
- [x] **I2:** Verify `from pytanga.viz import Visualizer, CameraConfig` works without errors
- [ ] **I3:** Verify all public names appear in `__all__`
- [ ] **I4:** Add `aiohttp>=3.9` to `pyproject.toml` dependencies (if not already present)

### 7.2 Error Handling & Robustness

- [x] **I5:** Add port conflict detection to `server.py` — `OSError` on address-in-use produces clear `RuntimeError` with remediation advice
- [x] **I6:** Add graceful SIGINT/SIGTERM shutdown to `visualizer.py` `run()` — `asyncio.Event` + signal handlers + `finally` cleanup
- [x] **I7:** Add browser-open fallback to `server.py` — `webbrowser.open()` wrapped in try/except, prints manual URL on failure
- [x] **I8:** Test port conflict: run two visualizers on same port → clear error message, no traceback spew
- [x] **I9:** Test Ctrl+C → server shuts down cleanly, prints "Visualizer shut down."

### 7.3 Camera Configuration End-to-End

- [x] **I10:** Verify `CameraConfig.to_dict()` produces correct JSON with only non-None fields
- [x] **I11:** Verify `SceneConfig.to_dict()` includes `camera` key when camera is configured
- [x] **I12:** Verify JS auto-fit logic respects explicit camera settings (position, target, fov)
- [x] **I13:** Test auto-fit camera (default `Visualizer()`) frames all entities
- [x] **I14:** Test explicit camera (`CameraConfig(position=(10,6,12), target=(0,0,0), fov=50)`) positions camera exactly as specified
- [x] **I15:** Test partial camera (`CameraConfig(position=(5,10,5))` only) — target, FOV, near, far auto-computed

### 7.4 MV Input Pipeline

- [x] **I16:** Test `viz.add(pga.point(5,0,0))` — MV analyzed via `analyze()`, entity added, renders correctly
- [x] **I17:** Test `viz.add(pga.plane(0,0,1,3), opacity=0.3)` — plane renders with correct orientation
- [x] **I18:** Test MV that resolves to multiple entities returns `list[str]`
- [x] **I19:** Test `viz.update_entity(id, new_mv)` — MV analyzed, entity geometry replaced
- [x] **I20:** Test `viz.update_entity(id, multi_entity_mv)` raises `ValueError`
- [x] **I21:** Test `viz.add(mv)` with explicit `opns=False` — IPNS interpretation works

### 7.5 Jupyter Notebook Support

- [x] **I22:** Jupyter: `Visualizer()` auto-detects environment, sets `open_browser=False`
- [x] **I23:** Jupyter: `viz.start()` runs server in background thread (non-blocking)
- [x] **I24:** Jupyter: `viz` as last cell expression renders inline iframe via `_repr_html_()`
- [x] **I25:** Jupyter: `viz.add(...)` + `viz.flush()` updates viewer live across multiple cells
- [x] **I26:** Jupyter: `viz.stop()` releases port, server thread exits

### 7.6 Smoke Test

- [x] **I27:** Run `dev/src/test_viz_smoke.py` — all entity types render, both camera modes work
- [x] **I28:** Run `dev/src/test_viz_play.py` — end-to-end interactive session works
- [x] **I29:** No Python tracebacks during normal operation
- [x] **I30:** No console errors in the browser

## 8. Verification Checklist

- [x] `from pytanga.viz import Visualizer, CameraConfig` works.
- [x] `Visualizer` appears in `pytanga.viz.__all__`.
- [x] `aiohttp` listed in `pyproject.toml`.
- [x] Port conflict produces a clear `RuntimeError` message.
- [x] Ctrl+C gracefully shuts down the server.
- [x] Browser auto-opens; if it fails, manual URL is printed.
- [x] `add()` with MV analyzes the MV via `pytanga.geometry.analyze()` and adds the resulting entity.
- [x] `add()` with MV that resolves to multiple entities returns a `list[str]`.
- [x] `update_entity()` with MV works correctly (MV analyzed → entity replaced).
- [x] `update_entity()` with multi-entity MV raises `ValueError`.
- [x] Smoke-test script renders all entity types (both Entity and MV input).
- [x] **Auto-fit:** camera frames all entities correctly with no explicit CameraConfig.
- [x] **Explicit camera:** `CameraConfig(position=..., fov=...)` positions camera exactly as specified.
- [x] **Partial camera:** Setting only `position` auto-computes target, FOV, near, far.
- [x] **Space extent:** `space_extent=25` produces a larger grid than default `10`.
- [x] **Jupyter:** `Visualizer()` in a notebook does not auto-open browser.
- [x] **Jupyter:** `viz` as last cell expression renders an iframe (`_repr_html_`).
- [x] **Jupyter:** `start()` + `flush()` + `stop()` cycle works across multiple cells.
- [x] **Jupyter:** Entities added in later cells appear in the already-open viewer.
- [x] No Python tracebacks during normal operation or shutdown.
- [x] No console errors in the browser.

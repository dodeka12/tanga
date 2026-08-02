# Phase 10: Runnable Example Scripts

**Files:** `py/examples/viz/` — 7 Python scripts + 1 Jupyter notebook

**Goal:** Provide a comprehensive set of runnable example scripts that demonstrate
every feature of the visualization submodule. These serve as both documentation and
smoke tests. Each script is self-contained and can be run with `uv run python`.

**Prerequisites:** Phase 7 (fully integrated package)

---

## 1. Example Scripts

### 1.1 `demo_all_entities.py` — All Entity Types

Displays every supported geometric entity in a single static scene.

```python
# py/examples/viz/demo_all_entities.py
"""Demonstrate all geometric entity types in a single scene.

Run with: uv run python py/examples/viz/demo_all_entities.py
"""

from pytanga.viz import Visualizer
from pytanga.geometry import (
    Circle, Direction, Line, Plane, Point, PointPair, Space, Sphere,
)

viz = Visualizer(title="Tanga — All Entity Types")

# Points at various positions
viz.add(Point(2, 0, 0), color="#ff4444", size=0.12, label="P₁ (2,0,0)")
viz.add(Point(0, 2, 0), color="#44ff44", size=0.12, label="P₂ (0,2,0)")
viz.add(Point(0, 0, 2), color="#4444ff", size=0.12, label="P₃ (0,0,2)")

# Direction arrow from origin
viz.add(Direction(1, 1, 0), color="#ffffff", length=3.0, label="d")

# Line through origin along X axis
viz.add(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    color="#44ff44", thickness=0.04, label="L (x-axis)",
)

# Translucent plane at z=3
viz.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    color="#4488ff", opacity=0.25, label="π (z=3)",
)

# Circle in XY plane
viz.add(
    Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=3),
    color="#ff44ff", label="C",
)

# Sphere at origin
viz.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    color="#ffaa00", wireframe=True, opacity=0.3, label="S",
)

# Point pair
viz.add(
    PointPair(point_a=Point(-1, 1, 0), point_b=Point(1, 1, 0)),
    color="#44ff44", label="PP",
)

# Space — faint bounding outline
viz.add(Space(), opacity=0.08)

print("Scene ready. Close the browser window or press Ctrl+C to exit.")
viz.run()
```

### 1.2 `demo_mv_visualization.py` — MV Input with PGA3 and N3

Shows `add()` accepting multivectors directly from both PGA3 and N3 (full CGA) algebras.
Demonstrates OPNS vs IPNS interpretation, and that the full MV→analyze→Entity pipeline
works transparently for all entity types.

```python
# py/examples/viz/demo_mv_visualization.py
"""Demonstrate visualizing multivectors (MVs) from PGA3 and N3 algebras.

MVs are analyzed internally by pytanga.geometry.analyze() to extract
geometric entities. This demo covers the full MV → Entity pipeline for:

  PGA3:  Point (OPNS + IPNS), Direction, Line, Plane
  N3:    Point, PointPair, Line, Circle, Plane, Sphere

Run with: uv run python py/examples/viz/demo_mv_visualization.py
"""

from pytanga.algebra import Algebra
from pytanga.viz import Visualizer
from pytanga.geometry import Direction, Point, analyze

pga = Algebra.from_name("PGA3")
n3 = Algebra.from_name("N3")
viz = Visualizer(title="Tanga — MV → Entity Pipeline")

# ═══════════════════════════════════════════════════════════════
# Part 1: PGA3 entities (projective sub-algebra, only einfi)
# ═══════════════════════════════════════════════════════════════

# Plane at z=3, normal pointing up (OPNS, grade-1 in PGA3)
viz.add(pga.plane(0, 0, 1, 3), opacity=0.3, label="Plane (PGA3, z=3)")

# Point at (5, 0, 0) — OPNS form (grade-3 trivector)
mv_pt_opns = pga.point(5, 0, 0)
viz.add(mv_pt_opns, color="#ff4444", size=0.15, opns=True, label="P (OPNS)")

# Same point — IPNS form (grade-1 vector, dual representation)
viz.add(
    pga.point(5, 0, 0),
    color="#44ff44", size=0.10, opns=False, label="P (IPNS)",
)

# Direction (ideal point at infinity) — IPNS
viz.add(
    pga.point(1, 0, 0),               # same factory, but direction =
    opns=False,                         # zero einf component in grade 1
    color="#ffffff", length=2.0, label="Dir (∞)",
)

# Line through origin along X axis (OPNS)
viz.add(
    pga.line_from_direction(Direction(1, 0, 0), Point(0, 0, 0)),
    color="#44ff44", label="L (x-axis)",
)

# ═══════════════════════════════════════════════════════════════
# Part 2: N3 entities (full conformal, einfi + eo)
# ═══════════════════════════════════════════════════════════════

# Point at (-3, 2, 0) in N3
viz.add(n3.point(-3, 2, 0), color="#ff8844", size=0.12, label="N3 Pt")

# Point pair
viz.add(n3.point_pair(-3, 0, 0, 0, 2, 0), color="#8844ff", label="PtPair")

# Line through origin + direction in N3
viz.add(n3.line_from_origin_direction(Direction(0, 1, 0)), color="#44ffff", label="N3 L")

# Circle in XY plane, center at (0,0,0), radius 2, normal Z
viz.add(n3.circle(0, 0, 0, 0, 0, 1, 2), color="#ff44ff", label="Circle")

# Plane at z=5 in N3
viz.add(n3.plane(0, 0, 1, 5), opacity=0.2, color="#ff88ff", label="N3 Plane")

# Sphere at (-2, 0, 0) with radius 1.5
viz.add(n3.sphere(-2, 0, 0, 1.5), wireframe=True, opacity=0.35, label="Sphere")

# ═══════════════════════════════════════════════════════════════
# Part 3: Explicit analyze() — show what the pipeline does
# ═══════════════════════════════════════════════════════════════

mv_sphere = n3.sphere(0, 3, 0, 1.0)
result = analyze(mv_sphere)
print(f"  MV analyzed to: {result}")
print(f"  Type: {type(result).__name__}")
print(f"  Entity center: {result.center}, radius: {result.radius}")

# Also add this sphere (equivalent to above add() call)
viz.add(mv_sphere, wireframe=True, opacity=0.5, color="#ffaa00", label="Analyzed S")

print()
print("Summary of the MV → Entity pipeline:")
print("  viz.add(mv, opns=True)   →   analyze(mv, opns=True)   →   Entity → JSON → Three.js")
print("  viz.add(mv, opns=False)  →   analyze(mv, opns=False)  →   Entity → JSON → Three.js")
print()
print("Red point = OPNS (grade-3 trivector), Green point = IPNS (grade-1 vector)")
print("Close the browser window or press Ctrl+C to exit.")
viz.run()
```

### 1.3 `demo_animation_orbit.py` — Frame-by-Frame Animation

A point orbits the Z-axis at 60 FPS using Python frame streaming.

```python
# py/examples/viz/demo_animation_orbit.py
"""Demonstrate frame-by-frame animation using Python frame streaming.

A point orbits the Z-axis at ~60 FPS. Uses the non-blocking start()/flush()
pattern so the animation loop runs in the main thread.

Run with: uv run python py/examples/viz/demo_animation_orbit.py
"""

import math
import time
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Direction, Line

viz = Visualizer(title="Tanga — Animated Orbit")
viz.start()  # Non-blocking: server runs in background

# Add a stationary line as reference (z-axis)
viz.add(
    Line(origin=Point(0, 0, -3), direction=Direction(0, 0, 1)),
    color="#444466", thickness=0.02, length=6.0, label="z-axis",
)

# The orbiting point
point_id = viz.add(
    Point(3, 0, 0),
    color="#ff4444", size=0.15, label="orbit",
)

# A trail point showing a slight phase offset
trail_id = viz.add(
    Point(3, 0, 0),
    color="#ff8844", size=0.08,
)

viz.flush()  # Push initial state

print("Animating for 10 seconds... Close the browser window to exit early.")
try:
    for frame in range(600):  # ~10 seconds at 60 FPS
        angle = frame * 0.05  # radians per frame
        x = 3 * math.cos(angle)
        y = 3 * math.sin(angle)

        viz.update_entity(point_id, Point(x, y, 0))

        # Trail follows with 15° phase offset
        trail_angle = angle - 0.26
        viz.update_entity(
            trail_id,
            Point(2.8 * math.cos(trail_angle), 2.8 * math.sin(trail_angle), 0),
        )

        viz.flush()
        time.sleep(1 / 60)
except KeyboardInterrupt:
    pass
finally:
    viz.stop()
    print("Animation stopped.")
```

### 1.4 `demo_animation_timeline.py` — Keyframe Animation with Timeline

Uses the browser-tweened keyframe system to orchestrate multiple animations.

```python
# py/examples/viz/demo_animation_timeline.py
"""Demonstrate keyframe animation with Timeline sequencer.

Entities fade in, move, and morph using browser-side tweening.
No per-frame Python loop needed.

Run with: uv run python py/examples/viz/demo_animation_timeline.py
"""

import time
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere, Plane, Direction

viz = Visualizer(title="Tanga — Keyframe Timeline")
viz.start()

# Add entities — initially invisible
p1 = viz.add(Point(0, 0, 0), color="#ff4444", size=0.12, opacity=0.0, label="P₁")
p2 = viz.add(Point(5, 0, 0), color="#44ff44", size=0.12, opacity=0.0, label="P₂")
s = viz.add(
    Sphere(Point(0, 0, 0), radius=1),
    wireframe=True, opacity=0.0, label="S",
)
plane = viz.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.0, label="π",
)

viz.flush()

# Build a timeline of keyframed animations
viz.timeline() \
    .wait(0.5) \
    .animate_to(p1, opacity=1.0, duration=0.3) \
    .animate_to(p2, opacity=1.0, duration=0.3, parallel=True) \
    .wait(0.3) \
    .animate_to(p1, position=(3, 2, 0), duration=1.5, easing="ease-out") \
    .animate_to(p2, position=(0, 3, 0), duration=2.0, parallel=True) \
    .wait(0.3) \
    .animate_to(s, opacity=0.4, duration=0.5) \
    .animate_to(s, position=(3, 2, 0), duration=1.5, parallel=True) \
    .wait(0.2) \
    .animate_to(plane, opacity=0.2, duration=0.5) \
    .play()

# Wait for the timeline to complete (~6 seconds total)
time.sleep(7)

print("Timeline complete.")
viz.stop()
```

### 1.5 `demo_labels.py` — Entity Labels

Shows labels with custom styling, inline updates, and removal.

```python
# py/examples/viz/demo_labels.py
"""Demonstrate entity labeling with CSS2D overlays.

Labels follow entities in 3D space but always face the camera.

Run with: uv run python py/examples/viz/demo_labels.py
"""

import time
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere, Plane, Direction

viz = Visualizer(title="Tanga — Labels")
viz.start()

# Default label styling
viz.add(
    Point(1, 2, 0), color="#ff4444", size=0.15,
    label="P₁",
)

# Custom label styling
origin_id = viz.add(
    Point(0, 0, 0), color="#ffff00", size=0.2,
    label="Origin",
    labelOffsetY=0.5,
    labelFontSize=18,
    labelColor="#ffff00",
    labelBackground="rgba(0, 0, 0, 0.8)",
)

# Label on a plane
viz.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.3, label="π (z=3)",
)

# Label on a wireframe sphere
viz.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    wireframe=True, opacity=0.4,
    label="S₁",
    labelOffsetY=2.8,
)

viz.flush()

# Demonstrate dynamic label update
print('Updating label in 5 seconds...')
time.sleep(5)
viz.update(origin_id, label="O", labelColor="#ff8888", labelFontSize=22)
viz.flush()

print('Removing label in 5 seconds...')
time.sleep(5)
viz.update(origin_id, label=None)
viz.flush()

print("Close the browser window or press Ctrl+C to exit.")
viz.stop()
```

### 1.6 `demo_camera_config.py` — Camera Configuration

Compares auto-fit vs. explicit vs. partial camera configurations.

```python
# py/examples/viz/demo_camera_config.py
"""Demonstrate camera configuration: auto-fit, explicit, and partial.

Run with: uv run python py/examples/viz/demo_camera_config.py
"""

from pytanga.viz import Visualizer, CameraConfig
from pytanga.geometry import Point, Sphere, Plane, Direction

# ── Scene 1: Auto-fit camera (default) ─────────────────────
print("Scene 1: Auto-fit camera (default)")
viz1 = Visualizer(title="Tanga — Auto-fit Camera")
viz1.add(Point(2, 0, 0), color="#ff4444", size=0.15)
viz1.add(Point(0, 2, 0), color="#44ff44", size=0.15)
viz1.add(Point(0, 0, 2), color="#4444ff", size=0.15)
viz1.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    wireframe=True, opacity=0.3,
)
viz1.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.25,
)
viz1.run()

# ── Scene 2: Full explicit camera ──────────────────────────
print("\nScene 2: Explicit camera (top-down view, narrow FOV)")
viz2 = Visualizer(
    title="Tanga — Explicit Camera",
    camera=CameraConfig(
        position=(0, 15, 0),   # looking straight down from above
        target=(0, 0, 0),
        fov=30,                # narrow FOV — "telephoto"
    ),
    space_extent=20,
)
viz2.add(Point(2, 0, 0), color="#ff4444", size=0.15, label="P₁")
viz2.add(Point(0, 2, 0), color="#44ff44", size=0.15, label="P₂")
viz2.add(Point(0, 0, 2), color="#4444ff", size=0.15, label="P₃")
viz2.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    wireframe=True, opacity=0.3,
)
viz2.run()

# ── Scene 3: Partial camera — position only ────────────────
print("\nScene 3: Partial camera — position set, target & FOV auto-computed")
viz3 = Visualizer(
    title="Tanga — Partial Camera",
    camera=CameraConfig(position=(10, 3, 0)),  # only position is explicit
)
viz3.add(Point(2, 0, 0), color="#ff4444", size=0.15, label="P₁")
viz3.add(Point(0, 2, 0), color="#44ff44", size=0.15, label="P₂")
viz3.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    wireframe=True, opacity=0.3,
)
viz3.run()

print("\nAll scenes complete.")
```

### 1.7 `demo_custom_defaults.py` — Custom Default Rendering Properties

Sets global default colors, line thickness, and plane extents.

```python
# py/examples/viz/demo_custom_defaults.py
"""Demonstrate custom default rendering properties.

Global defaults apply to all subsequently added entities unless
overridden per-entity.

Run with: uv run python py/examples/viz/demo_custom_defaults.py
"""

from pytanga.viz import Visualizer
from pytanga.geometry import Point, Direction, Line, Plane, Sphere

viz = Visualizer(title="Tanga — Custom Defaults")

# Change default colors
viz.set_default_color("point", (0.0, 1.0, 0.0))    # RGB tuple → green
viz.set_default_color("line", (0.0, 1.0, 1.0))      # RGB tuple → cyan
viz.set_default_color("plane", "#ff00ff")            # hex string → magenta
viz.set_default_color("sphere", "#ffaa00")           # amber (unchanged)

# Change default extents for infinite objects
viz.set_default_extent(
    line_length=30.0,
    line_thickness=0.06,
    plane_extent=15.0,
)

# These use the new defaults
viz.add(Point(2, 0, 0), size=0.15, label="green point (default)")
viz.add(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    label="cyan line (default)",
)
viz.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.25, label="magenta plane (default)",
)
viz.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    wireframe=True, opacity=0.3, label="amber sphere (default)",
)

# Per-entity override — red, ignores the global green default
viz.add(Point(0, 2, 0), color="#ff0000", size=0.15, label="red point (override)")

# Bulk-set multiple defaults at once
viz.set_defaults(
    color_sphere="#4488ff",     # change sphere to blue
    line_thickness=0.02,         # make lines thinner
)

# This sphere uses the new blue default
viz.add(
    Sphere(Point(5, 0, 0), radius=1),
    wireframe=True, opacity=0.3, label="blue sphere (default)",
)

print("Examine the defaults dict:")
print(viz.defaults)

viz.run()
```

### 1.8 `demo_notebook.ipynb` — Jupyter Notebook Example

A complete notebook demonstrating the interactive workflow with inline iframe display.

```json
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Tanga 3D Viewer — Jupyter Notebook Demo\n",
    "\n",
    "This notebook demonstrates the interactive 3D viewer inside Jupyter.\n",
    "The viewer runs as a background server with an inline `<iframe>` display."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pytanga.viz import Visualizer, CameraConfig\n",
    "from pytanga.geometry import Point, Direction, Line, Plane, Sphere\n",
    "\n",
    "# Create the visualizer — open_browser is auto-disabled in Jupyter\n",
    "viz = Visualizer(\n",
    "    space_extent=15,\n",
    "    camera=CameraConfig(fov=45),\n",
    ")\n",
    "viz.start()  # non-blocking: server runs in background thread\n",
    "print(f\"Viewer available at {viz.url}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Add Entities"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Add some entities\n",
    "viz.add(Point(2, 0, 0), color=\"#ff4444\", size=0.15, label=\"P₁\")\n",
    "viz.add(Point(0, 2, 0), color=\"#44ff44\", size=0.15, label=\"P₂\")\n",
    "viz.add(Point(0, 0, 2), color=\"#4444ff\", size=0.15, label=\"P₃\")\n",
    "\n",
    "viz.add(\n",
    "    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),\n",
    "    opacity=0.25, label=\"π (z=3)\",\n",
    ")\n",
    "\n",
    "viz.add(\n",
    "    Sphere(Point(0, 0, 0), radius=2.5),\n",
    "    wireframe=True, opacity=0.3, label=\"S\",\n",
    ")\n",
    "\n",
    "viz.flush()\n",
    "print(\"Entities added and flushed.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Display the Viewer\n",
    "\n",
    "The cell below renders the viewer as an inline iframe."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Display the viewer inline (triggers _repr_html_)\n",
    "viz"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Add More Entities Later\n",
    "\n",
    "The viewer updates live — no page reload needed."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "viz.add(\n",
    "    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),\n",
    "    color=\"#44ff44\", label=\"L (x-axis)\",\n",
    ")\n",
    "viz.flush()\n",
    "print(\"Line added — check the viewer!\")\n",
    "viz  # re-render the iframe"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Cleanup\n",
    "\n",
    "Always stop the server when done to free the port."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "viz.stop()\n",
    "print(\"Server stopped.\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.12.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
```

---

## 2. Design Decisions

1. **Self-contained scripts:** Each demo is a standalone `.py` file runnable with
   `uv run python py/examples/viz/demo_*.py`. No shared utilities, no imports
   between demos.

2. **One concept per script:** Each demo focuses on exactly one feature (all entities,
   MV input, orbit animation, timeline, labels, camera config, custom defaults).
   This makes them easy to read and reference.

3. **`run()` for scripts, `start()` for animation:** Static demos use the simple
   blocking `run()`. Animation demos use `start()` + loop + `stop()`. The notebook
   uses `start()` + `flush()` + `stop()`.

4. **Labels on everything:** Most entities carry a `label` so the viewer shows
   what each thing is. This also serves as a label demonstration.

5. **Notebook as JSON:** The `.ipynb` file is specified as raw JSON (per Jupyter
   notebook format) so it can be opened directly in Jupyter/VSCode without any
   conversion step.

6. **Existing example pattern:** Follows the established pattern from
   `py/examples/geometry/` (e.g., `pga3_entities.py`, `n3_entities.py`).

---

### 3.1 Directory & Script Creation

- [ ] **E1:** Create `py/examples/viz/` directory
- [ ] **E2:** Create `demo_all_entities.py` — static scene with all 9 entity kinds (Point, Direction, Line, Plane, Circle, Sphere, Space, PointPair, HPoint)
- [ ] **E3:** Create `demo_mv_visualization.py` — MV input from both PGA3 (Point, Direction, Line, Plane) and N3 (Point, PointPair, Line, Circle, Plane, Sphere) algebras
- [ ] **E4:** Create `demo_animation_orbit.py` — frame-by-frame 60 FPS orbit animation using `start()`/`update_entity()`/`flush()`/`stop()`
- [ ] **E5:** Create `demo_animation_timeline.py` — keyframe Timeline with fade-in, move, parallel animations
- [ ] **E6:** Create `demo_labels.py` — labels with custom styling, dynamic update, and removal
- [ ] **E7:** Create `demo_camera_config.py` — three scenes: auto-fit, explicit camera (top-down, narrow FOV), partial camera (position only)
- [ ] **E8:** Create `demo_custom_defaults.py` — global default colors (hex + RGB tuples), default extents, bulk `set_defaults()`, per-entity overrides
- [ ] **E9:** Create `demo_notebook.ipynb` — Jupyter notebook with background server, inline iframe, live updates across cells, cleanup
- [ ] **E10:** Each `.py` script has a docstring with run instructions (`uv run python py/examples/viz/demo_*.py`)
- [ ] **E11:** Each script is self-contained (no shared imports between demos)

### 3.2 Content Requirements

- [ ] **E12:** `demo_all_entities.py` — each entity carries a `label` so the viewer shows what each thing is
- [ ] **E13:** `demo_mv_visualization.py` — demonstrates OPNS vs IPNS interpretation side-by-side (red point OPNS, green point IPNS)
- [ ] **E14:** `demo_mv_visualization.py` — includes explicit `analyze()` call to show the pipeline output
- [ ] **E15:** `demo_animation_orbit.py` — animated reference line (z-axis) + orbiting point + trail point with phase offset
- [ ] **E16:** `demo_animation_timeline.py` — multiple staggered steps + `parallel=True` + `easing` parameter
- [ ] **E17:** `demo_labels.py` — demo defaults, custom styling, `update(label=...)`, `update(label=None)` to remove
- [ ] **E18:** `demo_camera_config.py` — three separate visualizer scenes run sequentially
- [ ] **E19:** `demo_custom_defaults.py` — prints `viz.defaults` dict to console
- [ ] **E20:** Notebook `.ipynb` uses `start()`/`flush()`/`stop()` pattern (no `run()`)
- [ ] **E21:** Notebook renders inline iframe via `_repr_html_()`

### 3.3 Manual Verification

- [ ] **E22:** Run `demo_all_entities.py` — all 9 entity kinds render without errors
- [ ] **E23:** Run `demo_mv_visualization.py` — OPNS and IPNS points visible, line, plane, circle, sphere from N3 render
- [ ] **E24:** Run `demo_animation_orbit.py` — point orbits smoothly for 10 seconds at ~60 FPS
- [ ] **E25:** Run `demo_animation_timeline.py` — all keyframed steps execute in correct sequence (~6 seconds)
- [ ] **E26:** Run `demo_labels.py` — labels appear, update after 5 seconds, remove after 5 more
- [ ] **E27:** Run `demo_camera_config.py` — three scenes appear sequentially with distinct camera views
- [ ] **E28:** Run `demo_custom_defaults.py` — green points, cyan line, magenta plane, blue sphere, red point override visible
- [ ] **E29:** Open `demo_notebook.ipynb` in Jupyter/VSCode — inline iframe, live updates across cells, cleanup works
- [ ] **E30:** All scripts use `viz.run()` or `start()`/`stop()` correctly — no leaks, no tracebacks
- [ ] **E31:** Browser opens and closes correctly for each script

## 4. Verification Checklist

- [ ] `demo_all_entities.py` renders all 9 entity kinds without errors.
- [ ] `demo_mv_visualization.py` shows OPNS and IPNS interpretations side by side.
- [ ] `demo_animation_orbit.py` animates smoothly at 60 FPS for 10 seconds.
- [ ] `demo_animation_timeline.py` executes all keyframed steps in correct sequence.
- [ ] `demo_labels.py` shows labels, updates one, removes one.
- [ ] `demo_camera_config.py` shows three distinct camera configurations.
- [ ] `demo_custom_defaults.py` respects global colors and extents while allowing overrides.
- [ ] `demo_notebook.ipynb` displays the inline iframe and survives multiple cells.
- [ ] Each script has a docstring with run instructions.
- [ ] All scripts use `viz.run()` or `start()`/`stop()` correctly (no leaks).
- [ ] Browser opens and closes correctly for each script.
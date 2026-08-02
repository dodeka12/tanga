# Phase 5 — Example: Two Spheres Intersection

A complete example script that demonstrates the interactive controls API. Two
spheres are rendered at fixed positions with a visible intersection. A slider
controls the position of the second sphere, and the scene updates in real time
as the user drags the slider.

References: [Overview](./README.md) | [Phase 4](./phase4-python-api-integration.md)

---

## 5.1 Scenario

Two spheres in 3D space, using the IPNS (N3 / CGA) algebra:

- **Sphere A**: Center at origin `(0, 0, 0)`, radius 1.0 (red, semi-transparent)
- **Sphere B**: Center on the X-axis, position controlled by slider, radius 1.3 (blue, semi-transparent)
- **Intersection circle**: Computed via the IPNS outer product ``S₁ ∧ S₂`` (2‑vector blade, yellow)

### Modes (via dropdown)

- `"Both"` — show both spheres + intersection
- `"Sphere A only"` — hide Sphere B and intersection
- `"Sphere B only"` — hide Sphere A and intersection
- `"Intersection only"` — hide both spheres, show only the intersection circle

### Controls

| Control | Kind | Group | Purpose |
|---------|------|-------|---------|
| `sphere_b_x` | Slider [-3.5, 3.5, step 0.02, default 2.5] | "Sphere B" (attached to Sphere B) | Move Sphere B along X-axis |
| `mode` | Dropdown (Both / Sphere A only / Sphere B only / Intersection only) | Viewport panel (bottom-right) | Switch display mode |
| `reset` | Button | Viewport panel (bottom-right) | Reset Sphere B position to default (2.5) and mode to "Both" |

The "Sphere B" group is **attached** to Sphere B (via `parent_id`), so its
title bar follows the sphere in 3D space. The user can click the title to
expand the slider. The viewport panel group containing `mode` and `reset` is a
fixed panel at `bottom-right`.

---

## 5.2 Mathematics: IPNS Intersection via Outer Product

The example uses the **IPNS (Inner Product Null Space)** representation from
the N3 basis (CGA / conformal geometric algebra).  In IPNS:

- A sphere is a 1‑vector (grade‑1 blade) in the N3 algebra.
- The **outer product** (*wedge*, ``^``) of two IPNS spheres yields their
  **intersection circle** as a 2‑vector (grade‑2 blade).
- When the spheres do not intersect, the resulting blade has an imaginary
  radius — the Visualizer's ``analyze()`` returns ``None`` in that case,
  which the script handles by hiding the intersection entity.

This follows the same pattern as ``dev/src/test_viz_animation_stream.py``,
but replaces the programmatic animation loop with an interactive slider::

    from pytanga.basis import BasisN3
    from pytanga.geometry import Geometry, Point, Sphere

    b = BasisN3()
    geo = Geometry(b, opns=False)  # IPNS mode

    s1_mv = geo.create(Sphere(Point(0, 0, 0), 1.0))   # fixed sphere
    s2_mv = geo.create(Sphere(Point(x, 0, 0), 1.3))   # moving sphere
    ci_mv = s1_mv ^ s2_mv                               # intersection circle

The Visualizer's ``add()`` / ``update_entity()`` methods accept the raw
multivector directly; ``analyze()`` is called internally to extract the
geometric entity for rendering.

When the spheres separate (distance > sum of radii), the MV still exists
algebraically but ``analyze()`` returns ``None``.  The script detects this by
checking the analysis result and sets ``opacity=0`` to hide the circle.

---

## 5.3 Python Script

Script location: ``py/examples/viz/two_spheres_interact.py``

```python
"""Two Spheres Intersection — Interactive Controls Demo (IPNS).

Two spheres with a visible intersection circle computed via IPNS outer
product in the N3 (CGA) algebra.  A slider moves Sphere B along the
X‑axis; the intersection circle updates in real time.

Run with:

    uv run python py/examples/viz/two_spheres_interact.py
"""

from __future__ import annotations

import asyncio

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere, Circle
from pytanga.geometry.entities import Entity as GeoEntity
from pytanga.viz import Visualizer


SPHERE_A_RADIUS = 1.0
SPHERE_B_RADIUS = 1.3
SPHERE_B_DEFAULT_X = 2.5
SPHERE_A_ID = "sphere_a"
SPHERE_B_ID = "sphere_b"
INTERSECTION_ID = "intersection_circle"


def _create_sphere_mv(geo: Geometry, x: float, y: float, z: float, r: float):
    """Create an IPNS sphere multivector."""
    return geo.create(Sphere(Point(x, y, z), r))


def _compute_intersection_mv(geo: Geometry, s1_mv, x: float):
    """Return the IPNS intersection circle MV for Sphere B at position *x*,
    or ``None`` if the spheres do not intersect (imaginary circle)."""
    s2_mv = _create_sphere_mv(geo, x, 0.0, 0.0, SPHERE_B_RADIUS)
    ci_mv = s1_mv ^ s2_mv
    # Check whether the blade represents a real geometric entity
    result = geo.which_entity(ci_mv)
    if result is None:
        return None, s2_mv
    return ci_mv, s2_mv


async def main() -> None:
    # ── Geometry setup (IPNS, N3 basis) ────────────────────
    b = BasisN3()
    geo = Geometry(b, opns=False)

    # ── Create visualizer ──────────────────────────────────
    viz = Visualizer(title="Two Spheres Intersection (IPNS)", space_extent=6, opns=False)
    viz.set_annotation("IPNS intersection $S_1 \\wedge S_2$ — drag the slider to move Sphere B.")
    viz.start()
    viz.wait_for_browser(timeout=30)

    # ── Fixed sphere A ─────────────────────────────────────
    s1_mv = _create_sphere_mv(geo, 0.0, 0.0, 0.0, SPHERE_A_RADIUS)
    viz.add(s1_mv, entity_id=SPHERE_A_ID, color="#ff4444", opacity=0.3,
            label="$S_1$ (fixed)")

    # ── Moving sphere B (initial position) ─────────────────
    s2_mv = _create_sphere_mv(geo, SPHERE_B_DEFAULT_X, 0.0, 0.0, SPHERE_B_RADIUS)
    viz.add(s2_mv, entity_id=SPHERE_B_ID, color="#4488ff", opacity=0.3,
            label="$S_2$ (moving)")

    # ── Initial intersection circle ────────────────────────
    ci_mv = s1_mv ^ s2_mv
    viz.add(ci_mv, entity_id=INTERSECTION_ID, color="#ffcc00",
            label="$S_1 \\wedge S_2$")

    viz.flush()

    # ── State ──────────────────────────────────────────────
    state = {"mode": "Both", "sphere_b_x": SPHERE_B_DEFAULT_X}

    # ── Handler: slider change ─────────────────────────────
    async def on_slider_change(value: float):
        state["sphere_b_x"] = value
        await update_scene(viz, geo, s1_mv, value, state["mode"])

    # ── Handler: dropdown mode change ──────────────────────
    async def on_mode_change(mode: str):
        state["mode"] = mode
        await update_scene(viz, geo, s1_mv, state["sphere_b_x"], mode)

    # ── Handler: reset button ──────────────────────────────
    async def on_reset(_):
        state["sphere_b_x"] = SPHERE_B_DEFAULT_X
        state["mode"] = "Both"
        await update_scene(viz, geo, s1_mv, SPHERE_B_DEFAULT_X, "Both")
        viz.clear_controls()
        _setup_controls(viz)

    # ── Register controls ──────────────────────────────────
    def _setup_controls(v: Visualizer):
        v.add_slider(
            "sphere_b_x",
            label="X Position",
            min=-3.5,
            max=3.5,
            step=0.02,
            default=SPHERE_B_DEFAULT_X,
            on_change=on_slider_change,
        )
        v.add_dropdown(
            "mode",
            label="Display",
            options=["Both", "Sphere A only", "Sphere B only", "Intersection only"],
            default="Both",
            on_change=on_mode_change,
        )
        v.add_button("reset", label="Reset", on_click=on_reset)
        v.add_group(
            "viewport_controls",
            title="",
            controls=["mode", "reset"],
            position="bottom-right",
        )
        v.add_group(
            "sphere_b_group",
            title="Sphere B",
            controls=["sphere_b_x"],
            parent_id=SPHERE_B_ID,
            collapsed=True,
        )

    _setup_controls(viz)

    # ── Block until keyboard interrupt ─────────────────────
    try:
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (2, 15):  # SIGINT, SIGTERM
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                pass
        await stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        viz.stop()
        print("Done.")


async def update_scene(
    viz: Visualizer,
    geo: Geometry,
    s1_mv,
    sphere_b_x: float,
    mode: str,
) -> None:
    """Re‑compute spheres + intersection and push to the viewer."""

    # ── Sphere B at new position ───────────────────────────
    s2_mv = _create_sphere_mv(geo, sphere_b_x, 0.0, 0.0, SPHERE_B_RADIUS)
    viz.update_entity(SPHERE_B_ID, s2_mv)

    # ── Intersection via IPNS outer product ────────────────
    ci_mv = s1_mv ^ s2_mv
    ci_exists = geo.which_entity(ci_mv) is not None

    # ── Apply display mode ─────────────────────────────────
    show_a = mode in ("Both", "Sphere A only")
    show_b = mode in ("Both", "Sphere B only")
    show_ci = mode in ("Both", "Intersection only")

    viz.update(SPHERE_A_ID, opacity=0.3 if show_a else 0.0)
    viz.update(SPHERE_B_ID, opacity=0.3 if show_b else 0.0)

    if show_ci and ci_exists:
        viz.update_entity(INTERSECTION_ID, ci_mv)
        viz.update(INTERSECTION_ID, opacity=0.9)
    else:
        viz.update(INTERSECTION_ID, opacity=0.0)

    viz.flush()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5.4 Expected Behavior

1. Browser opens with two semi-transparent spheres and a white intersection circle.
2. A viewport panel at bottom-right shows "Display" dropdown and "Reset" button.
3. A title bar "Sphere B" is attached to the blue sphere in 3D space. It is
   collapsed by default (arrow ▸).
4. Clicking "Sphere B" title bar expands the slider "X Position". The user
   drags the slider; Sphere B moves along the X-axis in real time, and the
   intersection circle updates.
5. Changing the "Display" dropdown to "Sphere A only" hides Sphere B and the
   intersection; switching back restores them.
6. Clicking "Reset" restores the default position and mode.
7. Orbit controls (rotate, pan, zoom) work normally and do not interfere with
   controls.

---

## 5.5 Verification Checklist

- [ ] 5.1 Script starts without errors, browser opens with two spheres and intersection circle
- [ ] 5.2 Viewport panel at bottom-right shows dropdown and button
- [ ] 5.3 Attached group "Sphere B" appears on blue sphere in 3D space
- [ ] 5.4 Clicking "Sphere B" expands the slider
- [ ] 5.5 Dragging the slider moves Sphere B and updates intersection circle smoothly
- [ ] 5.6 Changing the dropdown hides/shows the correct entities
- [ ] 5.7 Reset button restores default position and mode, slider resets to default
- [ ] 5.8 Orbit controls work without interference from control panel
- [ ] 5.9 Drag-and-move the viewport control panel to a different corner
- [ ] 5.10 Hide/restore toggle works for all controls
- [ ] 5.11 Moving Sphere B beyond intersection range causes the circle to disappear
- [ ] 5.12 Moving Sphere B back into range restores the circle at the correct position
- [ ] 5.13 Ctrl+C gracefully shuts down the server and closes the browser viewer
- [ ] 5.14 LaTeX math in annotation renders correctly (``$S_1 \\wedge S_2$``)
- [ ] 5.15 Entity labels (``$S_1$``, ``$S_2$``, ``$S_1 \\wedge S_2$``) appear and follow objects

---

## 5.6 Implementation Checklist

- [ ] 5.1 Create `py/examples/viz/two_spheres_interact.py`
- [ ] 5.2 Implement sphere rendering with wireframe style
- [ ] 5.3 Implement IPNS geometry setup: `BasisN3`, `Geometry(opns=False)`, `geo.create(Sphere(...))`
- [ ] 5.4 Implement `update_scene()` with IPNS outer product `s1_mv ^ s2_mv` and four display modes
- [ ] 5.5 Implement slider handler `on_slider_change()`
- [ ] 5.6 Implement dropdown handler `on_mode_change()`
- [ ] 5.7 Implement reset handler `on_reset()`
- [ ] 5.8 Implement attached control group for Sphere B
- [ ] 5.9 Implement viewport control panel for mode + reset
- [ ] 5.10 Run full manual verification against section 5.5 checklist
- [ ] 5.11 Document any bugs or edge cases found during testing
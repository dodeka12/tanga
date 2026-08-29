# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""objects.py — Mix standard meshes with SDF-styled objects.

Adds a normal (mesh) sphere and plane alongside a ray-marched SDF sphere and an
SDF-styled ``Composed`` "bead" (a sphere with a drilled hole), all in the
*standard* viewer. The bead tweens upward (exercising the transform-update
path) and the SDF sphere has a label + click interaction.

Run with:  uv run python py/examples/viz/sdf/objects.py

Keywords: SDF, meshes, styled objects
"""

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import (
    InteractionConfig,
    InteractionEventType,
    InteractionTrigger,
    SdfStyle,
    Visualizer,
)
from pytanga.viz.sdf import Composed, capped_cylinder, sphere

viz = Visualizer(title="Tanga — SDF objects in the standard viewer")
viz.show()

# ── Normal mesh objects (the unchanged vertex/mesh pipeline) ──
viz.add(Sphere(Point(-3.0, 0.0, 0.0), 1.0), color="#4477cc", label="mesh sphere")
viz.add(
    Plane(point=Point(0.0, -1.6, 0.0), normal=Direction(0.0, 1.0, 0.0)),
    opacity=0.3,
)

# ── SDF-styled sphere (ray-marched in the same scene) ─────────
sdf_sphere_id = viz.add(
    Sphere(Point(2.6, 0.0, 0.0), 1.1),
    style=SdfStyle(color="#ffaa00"),
    label="SDF sphere",
)

# ── SDF-styled Composed bead: a sphere with a drilled hole ────
# (per-object CSG only — the subtract cylinder carves the sphere's interior).
bead = Composed(
    sphere(0.7),
    (capped_cylinder(1.0, 0.45), "subtract"),
)
bead_id = viz.add(bead, style=SdfStyle(color="#44ff44"), label="SDF bead")

# ── Click interaction on the SDF sphere ──────────────────────
# Note: raycasting hits the proxy bounding box, so clicks slightly off the
# SDF surface may still register.
viz.set_interaction(
    sdf_sphere_id,
    InteractionConfig(
        enabled=True,
        triggers=[InteractionTrigger(InteractionEventType.CLICK)],
        hover_emissive="#052556",
        hover_scale=2.3,
        hover_opacity=1.0,
    ),
)


async def _on_click(event) -> None:
    pos = getattr(event, "world_position", None)
    print(f"SDF sphere clicked at {pos}")


viz.on_interaction(sdf_sphere_id, InteractionEventType.CLICK, _on_click)

viz.flush()

# ── Animate the bead upward (tween → transform-update path) ──
viz.animate_to(bead_id, position=(0.0, 1.4, 0.0), duration=2.0)

print("A blue mesh sphere + translucent plane, an orange SDF sphere, and a")
print("green SDF bead (sphere with a drilled hole) should be visible.")
print("The bead tweens upward; click the SDF sphere (console prints the hit).")
print("Close the browser window or press Ctrl+C to exit.")

viz.wait()

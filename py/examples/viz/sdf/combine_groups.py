# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""combine_groups.py — Combine multiple SdfGroups (nesting + merging).

``SdfGroup`` members may themselves be ``SdfGroup``/``Composed`` objects: a
nested group lowers to a fixed-tree snapshot, and a ``Composed`` can merge
several ``SdfGroup``s into a single combine tree. This example builds two
composite groups — a drilled ball and a smooth axle — then shows both ways of
combining them: one ``SdfGroup`` nested inside another, and the two merged with
``Composed``. Each combined object renders as one ray-marched solid.

Run with:  uv run python py/examples/viz/sdf/combine_groups.py

Keywords: SDF, SdfGroup, Composed, nesting, merge
"""

from pytanga.viz import SdfStyle, Visualizer
from pytanga.viz._nodes import Transform, VizGroup
from pytanga.viz.sdf import (
    Composed,
    ECompose,
    SdfCompose,
    SdfGroup,
    capped_cylinder,
    capsule,
    sphere,
)

viz = Visualizer(title="Tanga — Combining SDF groups")
viz.show()

# Group A: a ball with a cylinder bored through it.
ball = SdfGroup(
    sphere(1.0, id="ball"),
    SdfCompose(capped_cylinder(1.4, 0.4, id="bore"), ECompose.SUBTRACT),
)

# Group B: a capsule shaft capped by two balls, joined with a smooth union.
axle = SdfGroup(
    sphere(0.8, position=(-1.2, 0.0, 0.0), id="left"),
    SdfCompose(
        capsule((-2.2, 0.0, 0.0), (2.2, 0.0, 0.0), 0.35, 0.35, id="shaft"),
        ECompose.SMOOTH_UNION,
        smoothness=0.15,
    ),
    sphere(0.8, position=(1.2, 0.0, 0.0), id="right"),
)

# Nest: an SdfGroup whose members are themselves SdfGroups.
nested = SdfGroup(ball, axle)

# Merge: the same two groups folded into one Composed combine tree.
merged = Composed(ball, axle, id="merged")

grp = viz.new(VizGroup("nested", transform=Transform(position=(0, 2, 0))))
grp.add(nested, style=SdfStyle(color="#ffaa00"), label="nested SdfGroups")

viz.add(merged, style=SdfStyle(color="#44aaff"), label="merged SdfGroups")

viz.flush()

print("Two composite SdfGroups are combined in two ways:")
print("  - nested: an SdfGroup whose members are themselves SdfGroups")
print("  - merged: the same groups folded into one Composed combine tree")
print("Each renders as one ray-marched solid. Close the window or press Ctrl+C.")

viz.wait()

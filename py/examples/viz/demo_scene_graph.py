# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_scene_graph.py — Demonstrate ``VizGroup`` + direct transforms.

Builds a compound "spinner" (a group of points and lines), then animates it as
a unit via transform-only aspect patches while an independent element moves on
its own.  Transform-only changes re-serialize only the ``transform`` aspect —
no child geometry is recomputed or re-sent.

Run with:  uv run python py/examples/viz/demo_scene_graph.py
"""

import logging
import math

from pytanga.geometry import Direction, Line, Point
from pytanga.geometry.operators import Translator
from pytanga.viz import PointStyle, Visualizer

# Enable verbose WebSocket message-flow logging (see the reconnect/init trace).
# No module changes are needed: every ``tanga.*`` logger (server, visualizer)
# propagates to the root logger, so a single basicConfig() here redirects all
# of them to a file.  Set level=INFO for a quieter trace, DEBUG for the full
# connection/reconnection transcript.
# logging.basicConfig(
#     level=logging.DEBUG,
#     filename="_output/tanga_viz.log",
#     filemode="a",
#     encoding="utf-8",
#     format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
# )

viz = Visualizer(title="Tanga — Scene Graph")
viz.start()

# ── Compound object: a "spinner" group ──────────────────────
spinner = viz.add_group("spinner")
spinner.new(Point(0, 0, 0), color="#ff4444", label="hub")
spinner.new(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    color="#44aaff",
)
spinner.new(
    Line(origin=Point(0, 0, 0), direction=Direction(0, 1, 0)),
    color="#44ff44",
)
spinner.new(Point(1.5, 0, 0), color="#ffaa00", label="tip", style=PointStyle(size=0.10))

# ── Independent element for contrast ────────────────────────
roamer = viz.new(Point(0, 0, 3), color="#ffffff", label="roamer")
viz.flush()

print("Animating the scene graph for ~6 seconds...")
for frame in range(300):
    angle = frame * 0.03

    # Group-only transform aspect — children are NOT re-serialized.
    spinner.set_transform(rotation=(0.0, 0.0, angle))

    # Independent element moves in place (absolute position).
    roamer.set_transform(
        position=(
            1.5 * math.sin(frame * 0.02),
            0.0,
            3 + 1.5 * math.cos(frame * 0.02),
        )
    )

    # Showcase the operator-based transform API once per revolution.
    if frame % 120 == 0:
        spinner.apply_transform(Translator(vector=Direction(0.0, 0.0, 0.1)))

    viz.flush()
    viz.sleep_ms(20)

viz.stop()
print("Animation stopped.")

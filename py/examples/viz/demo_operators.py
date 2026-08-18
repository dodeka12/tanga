# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_operators.py — Rotor, Translator, Motor, Dilator visualization.

Run with:  uv run python py/examples/viz/demo_operators.py
"""

import math

from pytanga.geometry import Dilator, Direction, Motor, Point, Rotor, Translator
from pytanga.viz import Visualizer

viz = Visualizer(title="Tanga — Operators")

# Rotor: disc arc + axis line (90-degree rotation about Z)
viz.new(
    Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
    label="Rotor (pi/2, Z)",
)

# Translator: 3D arrow along X
viz.new(
    Translator(vector=Direction(2, 0, 0)),
    color="#44aaff",
    label="Translator (2, 0, 0)",
)

# Motor: helix curve showing combined rotation + translation
viz.new(
    Motor(
        rotor=Rotor(angle=math.pi * 1.5, axis=Direction(0, 0, 1)),
        translator=Translator(vector=Direction(0, 1, 0)),
    ),
    color="#ff66cc",
    label="Motor",
)

# Dilator: concentric expanding rings
viz.new(
    Dilator(factor=2.0, origin=Point(0, 0, 0)),
    color="#ffcc44",
    label="Dilator (x2)",
)

viz.show()
viz.wait()

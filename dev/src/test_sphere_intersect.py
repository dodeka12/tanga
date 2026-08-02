#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Interactive playground for pytanga.viz — modify and re-run to experiment.

Add any entities, operators, or MVs you want to visualize. The viewer opens
in your browser and stays open until you press Ctrl+C.

Run with:  uv run python dev/src/test_viz_play.py
"""

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere
from pytanga.viz import LabelStyle, SceneExporter, Visualizer


def main() -> None:

    N3 = BasisN3()
    geo = Geometry(N3, opns=False)
    s1 = geo.create(Sphere(Point(0, 0, 0), 1.0))
    s2 = geo.create(Sphere(Point(0.1, 0, 0), 2.0))

    s1.show("S1")
    s2.show("S2")

    s1_ana = geo.which_entity(s1)
    print(f"S1 analysis: {s1_ana}")
    s2_ana = geo.which_entity(s2)
    print(f"S2 analysis: {s2_ana}")

    c1 = s1 ^ s2
    c1.show("C1")

    c1_ana = geo.which_entity(c1)
    print(f"C1 analysis: {c1_ana}")

    c1d = c1.dual()


if __name__ == "__main__":
    main()

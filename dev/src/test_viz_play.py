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
    # ── Configure the scene ────────────────────────────────
    viz = Visualizer(
        # camera=CameraConfig(fov=45),  # uncomment for custom camera
        title="Sphere Intersections",
        opns=False,
    )
    viz.start()

    N3 = BasisN3()
    geo = Geometry(N3, opns=False)
    s1_mv = geo.create(Sphere(Point(0, 0, 0), 1.0))
    s2_mv = geo.create(Sphere(Point(1, 0, 0), 1.0))
    s3_mv = geo.create(Sphere(Point(0.5, 1, 0), 1.0))

    s1_mv.show("S1")
    s2_mv.show("S2")
    s3_mv.show("S3")

    s1_ana = geo.which_entity(s1_mv)
    print(f"S1 analysis: {s1_ana}")
    s2_ana = geo.which_entity(s2_mv)
    print(f"S2 analysis: {s2_ana}")
    s3_ana = geo.which_entity(s3_mv)
    print(f"S3 analysis: {s3_ana}")

    c1_mv = s1_mv ^ s2_mv
    pp1_mv = c1_mv ^ s3_mv

    c1_ana = geo.which_entity(c1_mv)
    print(f"C1 analysis: {c1_ana}")
    pp1_ana = geo.which_entity(pp1_mv)
    print(f"PP1 analysis: {pp1_ana}")

    # ── Add entities (edit / add / remove freely) ──────────
    # viz.add(Point(2, 0, 0), color="#ff4444", size=0.15, label="P₁")
    # viz.add(Point(0, 3, 0), color="#44ff44", size=0.15, label="P₂")
    # viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4, label="S")
    # viz.add(
    #     Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    #     opacity=0.3,
    #     label="π",
    # )

    viz.add(s1_mv, color="#ff4444", label="$S_1$")
    viz.add(s2_mv, color="#3620de", opacity="1.0", label="$S_2$")
    viz.add(s3_mv, color="#dd44ff", opacity="0.6", label="$S_3$")

    viz.add(c1_mv, color="#D1BF1D", label="$S_1\\wedge S_2$")
    eid, lid = viz.add(
        pp1_mv,
        color="#1AB03D",
        label="Point Pair",
        label_style=LabelStyle(offset_local=(-1.0, 0, 0), align=(0, 1)),
    )

    annotation = """
## Sphere Intersections

There are three spheres $S_1$, $S_2$ and $S_3$.
"""
    viz.set_annotation(annotation)

    steps = 100
    off_x = -1.0
    step = 2 / steps
    for _ in range(steps):
        off_x += step
        viz.update_label(
            lid,
            text=f"Point Pair offset {off_x:.2f}",
            style=LabelStyle(offset_local=(off_x, 0, 0)),
        )
        viz.flush()
        viz.sleep_ms(100)

    SceneExporter(viz).export_html("_output/test_viz.html", overwrite=True)
    # ── Open browser and block until Ctrl+C ────────────────
    viz.stop()


if __name__ == "__main__":
    main()

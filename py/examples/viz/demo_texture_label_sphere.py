# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Demo: Texture labels on spheres using plain text and KaTeX formulas.

Run::

    uv run python py/examples/viz/demo_texture_label_sphere.py
"""

from pytanga.geometry.entities import Point, Sphere
from pytanga.viz import SphereStyle, TextureLabelStyle, Visualizer


def main():
    viz = Visualizer(port=8765, open_browser=True)
    viz.set_title("Texture Labels on Spheres")

    # ── Sphere with plain text label ──
    viz.add(
        Sphere(Point(-5, 0, 0), 2.0),
        style=SphereStyle(
            color="#4488ff",
            opacity=0.6,
            wireframe=False,
            texture_label=TextureLabelStyle(
                text="Sphere A",
                repeat_u=2,
                repeat_v=1,
                offset_v=0,
                background="#ffffff",
                color="#000000",
                font_size=64,
                scale=0.5,
            ),
        ),
    )

    # ── Sphere with KaTeX formula label ──
    viz.add(
        Sphere(Point(0, 0, 0), 2.0),
        tex_label=r"$\mathcal{S}_1$",
        style=SphereStyle(
            color="#ff8844",
            opacity=0.6,
            wireframe=False,
        ),
    )

    # ── Sphere with mixed text + embedded formula ──
    viz.add(
        Sphere(Point(5, 0, 0), 2.0),
        style=SphereStyle(
            color="#44ff44",
            opacity=0.6,
            wireframe=False,
            texture_label=TextureLabelStyle(
                text="Radius $$r=2$$",
                repeat_u=2,
                repeat_v=1,
                offset_v=0,
                background=None,
                color="#000000",
                font_size=48,
                resolution=1024,
            ),
        ),
    )

    # ── Reference sphere without texture label ──
    viz.add(
        Sphere(Point(0, 4, 0), 1.0),
        style=SphereStyle(
            color="#ffaa00",
            opacity=0.4,
            wireframe=True,
        ),
    )

    print("Starting viewer — open your browser to http://localhost:8765")
    viz.run()


if __name__ == "__main__":
    main()

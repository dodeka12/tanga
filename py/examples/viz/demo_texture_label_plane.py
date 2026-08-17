# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Demo: Texture labels on planes with different align modes.

Run::

    uv run python py/examples/viz/demo_texture_label_plane.py
"""

from pytanga.geometry.entities import Direction, Plane, Point
from pytanga.viz import PlaneStyle, TextureLabelStyle, Visualizer


def main():
    viz = Visualizer(port=8766, open_browser=True)
    viz.set_title("Texture Labels on Planes")

    # ── Plane with "stretch" align (fills the quad) ──
    viz.new(
        Plane(Point(0, 0, 0), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#4488ff",
            opacity=0.3,
            extent=5.0,
            texture_label=TextureLabelStyle(
                text="Stretch Mode",
                align="stretch",
                # background="#ffffff",
                color="#333333",
                font_size=48,
            ),
        ),
    )

    # ── Plane with "fit" align (preserves aspect ratio) ──
    viz.new(
        Plane(Point(0, 0, 3), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#44ff44",
            opacity=0.3,
            extent=4.0,
            texture_label=TextureLabelStyle(
                text="Fit Mode",
                align="fit",
                # background="#ffffff",
                color="#333333",
                font_size=48,
            ),
        ),
    )

    # ── Plane with "repeat" align (tiled) ──
    viz.new(
        Plane(Point(0, 0, 6), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#ff8844",
            opacity=0.3,
            extent=4.0,
            texture_label=TextureLabelStyle(
                text="Tile",
                align="repeat",
                repeat_u=3,
                repeat_v=3,
                # background=None,
                color="#000000",
                font_size=48,
            ),
        ),
    )

    # ── Plane with mixed text + formula ──
    viz.new(
        Plane(Point(-6, 0, 3), Direction(1, 0, 0)),
        style=PlaneStyle(
            color="#ff44ff",
            opacity=0.3,
            extent=4.0,
            texture_label=TextureLabelStyle(
                text="Plane $$z=3$$ with $$\\mathbf{\\hat{n}}$$",
                math_mode=False,
                align="fit",
                background="#ffffff",
                color="#333333",
                font_size=36,
            ),
        ),
    )

    # ── Reference plane without texture label ──
    viz.new(
        Plane(Point(0, 0, 9), Direction(0, 0, 1)),
        style=PlaneStyle(
            color="#888888",
            opacity=0.15,
            extent=5.0,
            wireframe=True,
        ),
    )

    print("Starting viewer — open your browser to http://localhost:8766")
    viz.run()


if __name__ == "__main__":
    main()

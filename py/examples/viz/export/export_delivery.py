# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""export_delivery.py — Compare the three HTML delivery modes.

``delivery="offline"`` downloads and bundles third-party assets (three.js,
marked, KaTeX, html2canvas) at export time, so generating that file needs an
internet connection plus Node.js and esbuild.  The resulting HTML is fully
self-contained.

Run with:  uv run python py/examples/viz/export/export_delivery.py

Keywords: export, HTML, delivery, cdn, inline, offline
"""

from pathlib import Path

from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import PointStyle, SphereStyle, Visualizer

viz = Visualizer(title="Tanga — Delivery Modes")
viz.new(Point(2, 0, 0), color="#ff4444", style=PointStyle(size=0.15), label="$P_1$")
viz.new(Point(0, 2, 0), color="#44ff44", style=PointStyle(size=0.15), label="$P_2$")
viz.new(
    Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3
)
viz.new(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)

# Static exports read directly from the in-memory scene — no server needed.
viz.flush()

# ``cdn`` (default) loads the viewer runtime from jsDelivr, ``inline`` embeds
# the Tanga library, and ``offline`` downloads + bundles three.js/marked/KaTeX/
# html2canvas at export time (requires Node + esbuild) for a fully offline file.
for delivery in ("cdn", "inline", "offline"):
    path = Path(f"scene_{delivery}.html")
    viz.export_snapshot(str(path), overwrite=True, delivery=delivery)
    size_kb = path.stat().st_size / 1024
    print(f"{delivery:>7}: {path} ({size_kb:,.1f} KB)")

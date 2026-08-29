# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""multi_scene.py — Two named scenes, each shown in its own browser tab.

Demonstrates that ``VizSceneHandle`` is a context manager: ``with scene:``
resets the scene, calls ``show()`` on entry, and flushes on exit.  With
``reuse_existing=False``, each scene's ``show()`` opens a fresh browser tab
for that scene's URL (instead of waiting to reconnect an existing tab).

Run with:  uv run python py/examples/viz/scenes/multi_scene.py

Keywords: scenes, multi-scene, context manager, tabs
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Multi-Scene")

overview = viz.scene("overview", enable_server_stop_key=True)
detail = viz.scene("detail")

with overview:  # reset + show the overview tab, flush on exit
    overview.set_title("Overview")
    overview.add(Sphere(Point(0, 0, 0), radius=2), color="#4488ff", opacity=0.3)
    overview.add(Point(1, 1, 1), color="#ff4444")

with detail:  # reset + show the detail tab, flush on exit
    detail.set_title("Detail")
    detail.add(Sphere(Point(2, 1, 0), radius=1), color="#ffcc00", opacity=0.8)

print("Both scenes are shown in separate tabs. Press Ctrl+C to exit.")
viz.wait()

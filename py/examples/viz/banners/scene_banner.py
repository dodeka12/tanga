# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""scene_banner.py — Banners scoped to a named scene via ``VizSceneHandle``.

A ``VizSceneHandle`` (``viz.scene(name)``) exposes ``alert``, ``confirm``, and
``show_banner`` scoped to its scene, so a banner only appears over the pane(s)
showing that scene — unlike ``viz.alert(...)``, which is global.  This script
opens the scene handle in a tab and shows a global banner for contrast.

Run with:  uv run python py/examples/viz/banners/scene_banner.py

Keywords: banner, alert, confirm, scene, VizSceneHandle
"""

import time

from pytanga.geometry import Point, Sphere
from pytanga.viz import Button, Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Scene Banners")

detail = viz.scene("detail")

with detail:  # reset + show the detail tab, flush on exit
    detail.set_title("Detail")
    detail.add(Sphere(Point(0, 0, 0), radius=2), color="#4488ff", opacity=0.3)

# 1. Scene-scoped acknowledge banner — appears only over the "detail" scene.
bid = detail.alert("## Detail loaded\n\nThis is the **detail** scene.", title="Notice")
time.sleep(3)
detail.remove_banner(bid)

# 2. Scene-scoped yes / no / cancel.
bid = detail.confirm("Rebuild the detail scene?", title="Confirm")
time.sleep(3)
detail.remove_banner(bid)

# 3. Scene-scoped custom options.
bid = detail.show_banner(
    "Choose a view:",
    title="Options",
    controls=[
        Button(id="fit", label="Fit camera"),
        Button(id="top", label="Top view"),
    ],
)
time.sleep(3)
detail.remove_banner(bid)

# 4. For contrast: a global banner spans the whole viewport, not just "detail".
bid = viz.alert("Global alert — every scene sees this.", title="Global")
time.sleep(3)
viz.remove_banner(bid)

print("Scene-scoped banners shown in the 'detail' tab. Press Ctrl+C to exit.")
viz.wait()

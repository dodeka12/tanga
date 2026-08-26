# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""banner_types.py — Demonstrates every banner/dialog kind.

Run with:  uv run python py/examples/viz/banners/banner_types.py
"""

import time

from pytanga.geometry import Point
from pytanga.viz import Button, Visualizer

viz = Visualizer(title="Banner Types")
viz.new(Point(0, 0, 0), color="#ff4444")
viz.show()  # wait for the browser to connect so banners are actually received

# 1. Acknowledge banner — a single OK button (auto-hides on click).
bid = viz.alert("## Welcome\n\nThis is an **acknowledge** banner.", title="Notice")
time.sleep(3)
viz.remove_banner(bid)

# 2. Custom options — any control-group controls, laid out in the banner.
bid = viz.show_banner(
    "Choose an option:",
    title="Options",
    controls=[
        Button(id="opt_a", label="Option A"),
        Button(id="opt_b", label="Option B"),
    ],
    align_x=0.2,
    align_y=0.2,
)
time.sleep(3)
viz.remove_banner(bid)

# 3. Yes / No / Cancel convenience.
bid = viz.confirm("Proceed with the calculation?", title="Confirm")
time.sleep(3)
viz.remove_banner(bid)

# 4. Modal (non-dismissable) banner — blocks the scene until removed.
bid = viz.show_banner(
    "## Busy…\n\nComputing $e^{i\\pi} = -1$…",
    title="Working",
    dismissable=False,
)
time.sleep(3)
viz.remove_banner(bid)

viz.wait()

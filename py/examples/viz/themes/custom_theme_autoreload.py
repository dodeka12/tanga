# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""custom_theme_autoreload.py — Load a custom theme and edit it live.

Registers a custom theme from a local folder (``my_theme/`` next to this file),
switches to it, and enables automatic reloading so edits to its ``tokens.css``
or ``overrides/*.css`` appear in the browser without a page reload.

Run with:  uv run python py/examples/viz/themes/custom_theme_autoreload.py

Keywords: themes, theme, custom theme, register_theme, auto reload, tokens, override
"""

from pathlib import Path

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    EAnchor,
    GroupView,
    SceneView,
    SliderView,
    Visualizer,
    register_theme,
)

THEME_DIR = Path(__file__).parent / "my_theme"

register_theme("my_theme", THEME_DIR, label="My Theme")

viz = Visualizer(reuse_existing=False, title="Tanga — Custom Theme Auto-Reload")
viz.set_theme("my_theme")

viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#2ec4b6", opacity=0.3
)
viz.add(Point(1, 1, 1), color="#ff4444")


async def _on_radius(value, _event):
    viz.update_entity("sphere", Sphere(Point(0, 0, 0), radius=float(value)))
    viz.flush()


layout = SceneView(
    "",
    overlay=[
        GroupView(
            "Custom Theme",
            [
                SliderView(
                    "radius",
                    label="Radius",
                    min=0.1,
                    max=5.0,
                    value=2.0,
                    on_change=_on_radius,
                ),
                CheckboxView("wire", label="Wireframe", value=False),
                ButtonView("btn", label="Example Button"),
            ],
            position=EAnchor.TOP_LEFT,
        ),
    ],
)

viz.show(layout=layout)

# Enable auto-reload: edit my_theme/tokens.css or my_theme/overrides/*.css and
# the viewer restyles without a reload.
viz.enable_theme_auto_reload()
print(
    "Editing my_theme/tokens.css or my_theme/overrides/*.css reloads the theme "
    "live. Press Ctrl+C to exit."
)
viz.wait()

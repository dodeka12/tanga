# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""serve-value-edit-smoke.py — headless server for the value-edit focus smoke.

Builds a ``SceneView`` with a single ``ValueEditView`` overlay and prints the
URL for ``js/dev/tests/value-edit-focus-smoke.mjs``.  The smoke asserts that
hovering the stepper never focuses its input (so the scene keeps its keyboard
shortcuts) while clicking the field, label, or padding does — and that the
scroll wheel still steps the value on hover.

Run with:  uv run python js/dev/tests/serve-value-edit-smoke.py
"""

from typing import Any

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ControlEvent,
    EAnchor,
    GroupView,
    SceneView,
    ValueEditView,
    Visualizer,
)


def main() -> None:
    viz = Visualizer(
        title="Tanga — value edit focus smoke",
        add_default_axes=False,
        add_default_grid=False,
    )
    viz.add(Sphere(Point(0, 0, 0), radius=1.0), entity_id="ball", color="#4488ff")

    async def _on_radius(value: Any, _event: ControlEvent) -> None:
        viz.update_entity("ball", Sphere(Point(0, 0, 0), radius=float(value)))
        viz.flush()

    viz.set_layout(
        SceneView(
            "scene",
            overlay=[
                GroupView(
                    "Values",
                    [
                        ValueEditView(
                            "radius_value",
                            label="Radius",
                            min=0.3,
                            max=3.0,
                            step=0.05,
                            digits=2,
                            value=1.0,
                            editable=True,
                            on_change=_on_radius,
                        )
                    ],
                    position=EAnchor.TOP_LEFT,
                )
            ],
        )
    )

    viz.start_server(host="localhost", port=0)
    print(f"SMOKE_URL={viz.url}", flush=True)
    viz.wait()


if __name__ == "__main__":
    main()

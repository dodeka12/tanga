"""Two Spheres Intersection — Interactive Controls Demo (IPNS).

Two spheres with a visible intersection circle computed via IPNS outer
product in the N3 (CGA) algebra.  A slider moves Sphere B along the
X‑axis; the intersection circle updates in real time.

Demonstrates the :class:`~pytanga.viz.VisualizerApp` base class.

Run with:

    uv run python py/examples/viz/interaction/two_spheres_interact.py

Keywords: interaction, IPNS, spheres, slider, dropdown, VisualizerApp
"""

from __future__ import annotations

from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Sphere
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    DropdownView,
    GroupView,
    SceneView,
    SliderView,
    VisualizerApp,
)

SPHERE_A_ID = "sphere_a"
SPHERE_B_ID = "sphere_b"
INTERSECTION_ID = "intersection_circle"


class TwoSpheresApp(VisualizerApp):
    """Two IPNS spheres + wedge-product intersection circle with interactive
    slider, dropdown, reset button, and quit button.

    State is stored as plain instance attributes — accessible from all
    handler methods via ``self``.
    """

    def __init__(self) -> None:
        super().__init__(title="Two Spheres Intersection (IPNS)")
        # ── App state (used by handlers) ──
        self.radius_a = 1.0
        self.radius_b = 1.3
        self.x_default = 2.5
        self.mode: str = "Both"

    # ── lifecycle ───────────────────────────────────────────

    async def init(self) -> None:
        """Create the geometry, add entities, and register controls."""
        b = BasisN3(opns=False)
        self._geo = Geometry(b)

        self.viz.set_annotation(
            "IPNS intersection $S_1 \\wedge S_2$ — drag the slider to move Sphere B."
        )

        # ── Store initial MVs so handlers can reuse them ──
        # _geo(...) creates for Entity/Operator args; analyzes for MV args
        self._s1_mv = self._geo.create(Sphere(Point(0.0, 0.0, 0.0), self.radius_a))
        # _geo(...) creates for Entity/Operator args; analyzes for MV args
        s2_mv = self._geo.create(Sphere(Point(self.x_default, 0.0, 0.0), self.radius_b))
        ci_mv = self._s1_mv ^ s2_mv
        # _geo(...) creates for Entity/Operator args; analyzes for MV args
        print(self._geo.which_entity(ci_mv))

        self.viz.add(
            self._s1_mv,
            entity_id=SPHERE_A_ID,
            color="#ff4444",
            opacity=0.3,
            label="$S_1$ (fixed)",
        )
        self.viz.add(
            s2_mv,
            entity_id=SPHERE_B_ID,
            color="#4488ff",
            opacity=0.3,
            label="$S_2$ (moving)",
        )
        self.viz.add(
            ci_mv,
            entity_id=INTERSECTION_ID,
            color="#ffcc00",
            label="$S_1 \\wedge S_2$",
        )
        self.viz.flush()
        self._setup_controls()

    # ── handlers ────────────────────────────────────────────

    async def on_slider(self, value: float, _event: ControlEvent) -> None:
        self.x_default = value
        await self._update_scene(value, self.mode)

    async def on_mode(self, mode: str, _event: ControlEvent) -> None:
        self.mode = mode
        await self._update_scene(self.x_default, mode)

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self.x_default = 2.5
        self.mode = "Both"
        await self._update_scene(2.5, "Both")
        self._setup_controls()

    async def on_quit(self, _value: None, _event: ControlEvent) -> None:
        self.request_shutdown()

    # ── internal helpers ────────────────────────────────────

    def _setup_controls(self) -> None:
        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "",
                        [
                            SliderView(
                                "sphere_b_x",
                                label="X Position",
                                min=-3.5,
                                max=3.5,
                                step=0.02,
                                value=self.x_default,
                                on_change=self.on_slider,
                            ),
                            DropdownView(
                                "mode",
                                label="Display",
                                options=["Both", "Sphere A only", "Sphere B only", "Intersection only"],
                                value="Both",
                                on_change=self.on_mode,
                            ),
                            ButtonView("reset", label="Reset", on_click=self.on_reset),
                            ButtonView("quit", label="Quit", on_click=self.on_quit),
                        ],
                        position="bottom-right",
                    )
                ],
            )
        )

    async def _update_scene(self, x: float, mode: str) -> None:
        # _geo(...) creates for Entity/Operator args; analyzes for MV args
        s2_mv = self._geo.create(Sphere(Point(x, 0.0, 0.0), self.radius_b))
        self.viz.update_entity(SPHERE_B_ID, s2_mv)

        ci_mv = self._s1_mv ^ s2_mv
        # _geo(...) creates for Entity/Operator args; analyzes for MV args
        ci_exists = self._geo.which_entity(ci_mv) is not None

        show_a = mode in ("Both", "Sphere A only")
        show_b = mode in ("Both", "Sphere B only")
        show_ci = mode in ("Both", "Intersection only")

        self.viz.update(SPHERE_A_ID, opacity=0.3 if show_a else 0.0)
        self.viz.update(SPHERE_B_ID, opacity=0.3 if show_b else 0.0)

        if show_ci and ci_exists:
            self.viz.update_entity(INTERSECTION_ID, ci_mv)

        self.viz.flush()


if __name__ == "__main__":
    TwoSpheresApp().run()

# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""all_controls.py — Showcase every interactive control in one app.

Creates one of each control kind — slider, dropdown, button (with icon and
icon-only variants), text field, text area, color picker, checkbox, and file
chooser — grouped into titled panels with icons and tooltips, plus a
full-screen text editor (`open_editor`).  Each handler updates either the
sphere or the viewport annotation, so the effect of every control is visible.

Run with:  uv run python py/examples/viz/interaction/all_controls.py
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import ControlEvent, EIconMaterial, EIconUC, VisualizerApp


class AllControlsApp(VisualizerApp):
    """A single sphere driven by one of every control kind."""

    def __init__(self) -> None:
        super().__init__(title="All Controls")
        self._color = "#4488ff"
        self._radius = 1.0
        self._annotation = (
            "Every control is wired up — tweak them and watch the sphere / "
            "annotation respond."
        )

    # ── lifecycle ───────────────────────────────────────────

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0.0, 0.0, 0.0), self._radius),
            entity_id="ball",
            color=self._color,
            opacity=0.9,
            label="The ball",
        )
        self._set_annotation(self._annotation)
        self._setup_controls()
        self.viz.flush()

    # ── handlers ────────────────────────────────────────────

    async def on_radius(self, value: float, _event: ControlEvent) -> None:
        self._radius = value
        self.viz.update_entity("ball", Sphere(Point(0.0, 0.0, 0.0), value))
        self.viz.flush()

    async def on_color(self, value: str, _event: ControlEvent) -> None:
        self._color = value
        self.viz.update("ball", color=value)
        self.viz.flush()

    async def on_wireframe(self, value: bool, _event: ControlEvent) -> None:
        self.viz.update("ball", wireframe=value)
        self.viz.flush()

    async def on_mode(self, value: str, _event: ControlEvent) -> None:
        opacity = {"Solid": 0.9, "Translucent": 0.35, "Hidden": 0.0}[value]
        self.viz.update("ball", opacity=opacity)
        self.viz.flush()

    async def on_name(self, value: str, _event: ControlEvent) -> None:
        self._set_annotation(f"Name: {value}")

    async def on_notes(self, value: str, _event: ControlEvent) -> None:
        self._set_annotation(f"Notes: {value}")

    async def on_file(self, value: str, _event: ControlEvent) -> None:
        self._set_annotation(f"File: `{value}`")

    async def on_poke(self, _value: None, _event: ControlEvent) -> None:
        self._set_annotation("Poke!")

    async def on_edit_annotation(self, _value: None, _event: ControlEvent) -> None:
        self.viz.open_editor(
            "annotation_editor",
            label="Edit annotation",
            value=self._annotation,
            on_close=self.on_editor_close,
        )

    async def on_editor_close(
        self, text: str | None, _event: ControlEvent
    ) -> None:
        if text is not None:
            self._set_annotation(text)

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self._color = "#4488ff"
        self._radius = 1.0
        self.viz.update_entity("ball", Sphere(Point(0.0, 0.0, 0.0), 1.0))
        self.viz.update("ball", color=self._color, opacity=0.9, wireframe=False)
        self._set_annotation("Reset to defaults.")
        self.viz.flush()

    async def on_quit(self, _value: None, _event: ControlEvent) -> None:
        self.request_shutdown()

    # ── helpers ─────────────────────────────────────────────

    def _set_annotation(self, text: str) -> None:
        """Update the annotation and remember it as the editor's initial text."""
        self._annotation = text
        self.viz.set_annotation(text)

    # ── controls ────────────────────────────────────────────

    def _setup_controls(self) -> None:
        self.viz.add_slider(
            "radius",
            label="Radius",
            min=0.3,
            max=3.0,
            step=0.05,
            default=self._radius,
            tooltip="Scale the sphere",
            on_change=self.on_radius,
        )
        self.viz.add_dropdown(
            "mode",
            label="Appearance",
            options=["Solid", "Translucent", "Hidden"],
            default="Solid",
            tooltip="Switch the material",
            on_change=self.on_mode,
        )
        self.viz.add_color_picker(
            "color",
            label="Color",
            default=self._color,
            tooltip="Sphere color",
            on_change=self.on_color,
        )
        self.viz.add_checkbox(
            "wireframe",
            label="Wireframe",
            default=True,
            tooltip="Toggle wireframe",
            on_change=self.on_wireframe,
        )
        self.viz.add_text_field(
            "name",
            label="Name",
            value="The ball",
            placeholder="Type a name…",
            tooltip="Echoed to the annotation",
            on_change=self.on_name,
        )
        self.viz.add_text_area(
            "notes",
            label="Notes",
            value="",
            placeholder="Multi-line notes… ($x^2$ renders as math)",
            rows=3,
            tooltip="Echoed to the annotation (supports $…$ math)",
            on_change=self.on_notes,
        )
        self.viz.add_file_chooser(
            "data_file",
            label="Data file",
            placeholder="/path/to/file",
            tooltip="Pick a file",
            on_change=self.on_file,
        )
        self.viz.add_button(
            "edit_annotation",
            label="Edit annotation",
            icon=EIconUC.PENCIL,
            tooltip="Edit the annotation in a full editor",
            on_click=self.on_edit_annotation,
        )
        self.viz.add_button(
            "poke",
            label="Poke",
            icon=EIconMaterial.PLAY_ARROW,
            tooltip="Do something",
            on_click=self.on_poke,
        )
        self.viz.add_button(
            "reset",
            label="Reset",
            icon=EIconMaterial.REFRESH,
            tooltip="Reset everything",
            on_click=self.on_reset,
        )
        self.viz.add_button(
            "quit",
            icon=EIconUC.CLOSE,
            icon_only=True,
            tooltip="Quit",
            on_click=self.on_quit,
        )
        self.viz.add_control_group(
            "appearance",
            title="Appearance",
            icon=EIconUC.GEAR,
            tooltip="Shape and material",
            controls=["radius", "mode", "color", "wireframe", "name"],
            position="bottom-right",
        )
        self.viz.add_control_group(
            "text_files",
            title="Text & files",
            icon="material:edit",  # raw-string icon (same as the enum form)
            controls=["notes", "data_file"],
            position="top-right",
        )
        self.viz.add_control_group(
            "actions",
            title="Actions",
            icon=EIconMaterial.SETTINGS,
            controls=["edit_annotation", "poke", "reset", "quit"],
            position="top-left",
        )


if __name__ == "__main__":
    AllControlsApp().run()


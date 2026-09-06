# Showcase every interactive control in one app

**Keywords:** controls · slider · dropdown · button · VisualizerApp

Creates one of each control kind — slider, dropdown, button (with icon and
icon-only variants), text field, text area, color picker, checkbox, and file
chooser — grouped into titled `GroupView` panels with icons and tooltips,
plus a full-screen text editor (`open_editor`).  Each handler updates either
the sphere or the viewport annotation, so the effect of every control is
visible.  Two synced radius sliders, a stepper value-edit, and a live readout
text field demonstrate programmatic value updates (`*View.set_value`).

## Run

```bash
uv run python py/examples/viz/ui/controls/all_controls.py
```

## Source

[`viz/ui/controls/all_controls.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/all_controls.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""all_controls.py — Showcase every interactive control in one app.

Creates one of each control kind — slider, dropdown, button (with icon and
icon-only variants), text field, text area, color picker, checkbox, and file
chooser — grouped into titled ``GroupView`` panels with icons and tooltips,
plus a full-screen text editor (`open_editor`).  Each handler updates either
the sphere or the viewport annotation, so the effect of every control is
visible.  Two synced radius sliders, a stepper value-edit, and a live readout
text field demonstrate programmatic value updates (`*View.set_value`).

Run with:  uv run python py/examples/viz/ui/controls/all_controls.py

Keywords: controls, slider, dropdown, button, VisualizerApp
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    ColorPickerView,
    ControlEvent,
    DropdownView,
    EIconMaterial,
    EIconUC,
    FileChooserView,
    GroupView,
    SceneView,
    SliderView,
    TextAreaView,
    TextFieldView,
    ValueEditView,
    VisualizerApp,
)


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
        self._apply_radius(value)
        self._radius2_view.set_value(value)
        self._radius_value_view.set_value(value)
        self._radius_display_view.set_value(f"{value:.2f}")

    async def on_radius2(self, value: float, _event: ControlEvent) -> None:
        self._apply_radius(value)
        self._radius_view.set_value(value)
        self._radius_value_view.set_value(value)
        self._radius_display_view.set_value(f"{value:.2f}")

    async def on_radius_value(self, value: float, _event: ControlEvent) -> None:
        self._apply_radius(value)
        self._radius_view.set_value(value)
        self._radius2_view.set_value(value)
        self._radius_display_view.set_value(f"{value:.2f}")

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

    async def on_editor_close(self, text: str | None, _event: ControlEvent) -> None:
        if text is not None:
            self._set_annotation(text)

    async def on_reset(self, _value: None, _event: ControlEvent) -> None:
        self._color = "#4488ff"
        self._radius = 1.0
        self.viz.update_entity("ball", Sphere(Point(0.0, 0.0, 0.0), 1.0))
        self.viz.update("ball", color=self._color, opacity=0.9, wireframe=False)
        self._set_annotation("Reset to defaults.")
        self.viz.flush()
        self._radius_view.set_value(self._radius)
        self._radius2_view.set_value(self._radius)
        self._radius_value_view.set_value(self._radius)
        self._radius_display_view.set_value(f"{self._radius:.2f}")
        self._mode_view.set_value("Solid")
        self._color_view.set_value(self._color)
        self._wireframe_view.set_value(False)

    async def on_quit(self, _value: None, _event: ControlEvent) -> None:
        self.request_shutdown()

    # ── helpers ─────────────────────────────────────────────

    def _set_annotation(self, text: str) -> None:
        """Update the annotation and remember it as the editor's initial text."""
        self._annotation = text
        self.viz.set_annotation(text)

    def _apply_radius(self, value: float) -> None:
        """Resize the sphere and remember the shared radius."""
        self._radius = value
        self.viz.update_entity("ball", Sphere(Point(0.0, 0.0, 0.0), value))
        self.viz.flush()

    # ── controls ────────────────────────────────────────────

    def _setup_controls(self) -> None:
        self._radius_view = SliderView(
            "radius",
            label="Radius",
            min=0.3,
            max=3.0,
            step=0.05,
            value=self._radius,
            tooltip="Scale the sphere",
            on_change=self.on_radius,
        )
        self._radius2_view = SliderView(
            "radius2",
            label="Radius 2",
            min=0.3,
            max=3.0,
            step=0.05,
            value=self._radius,
            tooltip="Also scales the sphere (synced with Radius)",
            on_change=self.on_radius2,
        )
        self._radius_value_view = ValueEditView(
            "radius_value",
            label="Radius (stepper)",
            min=0.3,
            max=3.0,
            step=0.05,
            digits=2,
            value=self._radius,
            editable=True,
            tooltip="Increment with buttons, arrow keys, or the scroll wheel; type to edit",
            on_change=self.on_radius_value,
        )
        self._radius_display_view = TextFieldView(
            "radius_display",
            label="Radius value",
            value=f"{self._radius:.2f}",
            tooltip="Live value of the radius sliders",
        )
        self._mode_view = DropdownView(
            "mode",
            label="Appearance",
            options=["Solid", "Translucent", "Hidden"],
            value="Solid",
            tooltip="Switch the material",
            on_change=self.on_mode,
        )
        self._color_view = ColorPickerView(
            "color",
            label="Color",
            value=self._color,
            tooltip="Sphere color",
            on_change=self.on_color,
        )
        self._wireframe_view = CheckboxView(
            "wireframe",
            label="Wireframe",
            value=True,
            tooltip="Toggle wireframe",
            on_change=self.on_wireframe,
        )
        name_view = TextFieldView(
            "name",
            label="Name",
            value="The ball",
            placeholder="Type a name…",
            tooltip="Echoed to the annotation",
            on_change=self.on_name,
        )
        notes_view = TextAreaView(
            "notes",
            label="Notes",
            value="",
            placeholder="Multi-line notes… ($x^2$ renders as math)",
            rows=3,
            tooltip="Echoed to the annotation (supports $…$ math)",
            on_change=self.on_notes,
        )
        data_file_view = FileChooserView(
            "data_file",
            label="Data file",
            placeholder="/path/to/file",
            tooltip="Pick a file",
            on_change=self.on_file,
        )
        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "Appearance",
                        [
                            self._radius_view,
                            self._radius2_view,
                            self._radius_value_view,
                            self._radius_display_view,
                            self._mode_view,
                            self._color_view,
                            self._wireframe_view,
                            name_view,
                        ],
                        icon=EIconUC.GEAR,
                        tooltip="Shape and material",
                        position="bottom-right",
                    ),
                    GroupView(
                        "Text & files",
                        [notes_view, data_file_view],
                        icon="material:edit",  # raw-string icon (same as the enum form)
                        position="top-right",
                    ),
                    GroupView(
                        "Actions",
                        [
                            ButtonView(
                                "edit_annotation",
                                label="Edit annotation",
                                icon=EIconUC.PENCIL,
                                tooltip="Edit the annotation in a full editor",
                                on_click=self.on_edit_annotation,
                            ),
                            ButtonView(
                                "poke",
                                label="Poke",
                                icon=EIconMaterial.PLAY_ARROW,
                                tooltip="Do something",
                                on_click=self.on_poke,
                            ),
                            ButtonView(
                                "reset",
                                label="Reset",
                                icon=EIconMaterial.REFRESH,
                                tooltip="Reset everything",
                                on_click=self.on_reset,
                            ),
                            ButtonView(
                                "quit",
                                icon=EIconUC.CLOSE,
                                icon_only=True,
                                tooltip="Quit",
                                on_click=self.on_quit,
                            ),
                        ],
                        icon=EIconMaterial.SETTINGS,
                        position="top-left",
                    ),
                ],
            )
        )


if __name__ == "__main__":
    AllControlsApp().run()
````

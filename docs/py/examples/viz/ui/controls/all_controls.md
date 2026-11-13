# Showcase every interactive control in one app

**Keywords:** params view · nested group · hide · show · visible · theme · tooltip

Creates one of each control kind — slider, dropdown, button (with icon and
icon-only variants), text field, text area, color picker, checkbox, and file
chooser — grouped into titled `GroupView` panels with icons, plus a
full-screen text editor (`open_editor`).  Each handler updates either the
sphere or the viewport annotation, so the effect of every control is visible.
Two synced radius sliders, a stepper value-edit, and a live readout text field
demonstrate programmatic value updates (`*View.set_value`).

Every control, group, and menu carries a `tooltip=` text.  A permanent menu
bar on top holds a **Help → Show tooltips** option that calls
`Visualizer.set_tooltips_enabled` to hide/show every framework tooltip
page-wide (the label stays visible, so the option can always be found again),
plus a **Theme** menu that switches the whole UI between the `dark` and
`compact` themes.

A **Visibility** menu hides and shows things at runtime without re-pushing the
layout: a whole `GroupView` pane (title included), a single control inside a
group, one `ParamsView` row (label + control), and the nested `Shape`
sub-panel of the `ParamsView`.  A hidden pane disappears from the surrounding
stack and a hidden row takes neither height nor gap, so the layout closes up.

A `ParamsView` in the bottom-left panel demonstrates nested field groups and
the group variants: its `Shape` sub-group is explicitly `tiny`, while the
other field groups would default to `small`.  Hovering a value row's label
shows the control's tooltip, and clicking any group header folds it.

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
chooser — grouped into titled ``GroupView`` panels with icons, plus a
full-screen text editor (`open_editor`).  Each handler updates either the
sphere or the viewport annotation, so the effect of every control is visible.
Two synced radius sliders, a stepper value-edit, and a live readout text field
demonstrate programmatic value updates (`*View.set_value`).

Every control, group, and menu carries a ``tooltip=`` text.  A permanent menu
bar on top holds a **Help → Show tooltips** option that calls
``Visualizer.set_tooltips_enabled`` to hide/show every framework tooltip
page-wide (the label stays visible, so the option can always be found again),
plus a **Theme** menu that switches the whole UI between the ``dark`` and
``compact`` themes.

A **Visibility** menu hides and shows things at runtime without re-pushing the
layout: a whole ``GroupView`` pane (title included), a single control inside a
group, one ``ParamsView`` row (label + control), and the nested ``Shape``
sub-panel of the ``ParamsView``.  A hidden pane disappears from the surrounding
stack and a hidden row takes neither height nor gap, so the layout closes up.

A ``ParamsView`` in the bottom-left panel demonstrates nested field groups and
the group variants: its ``Shape`` sub-group is explicitly ``tiny``, while the
other field groups would default to ``small``.  Hovering a value row's label
shows the control's tooltip, and clicking any group header folds it.

Run with:  uv run python py/examples/viz/ui/controls/all_controls.py

Keywords: params view, nested group, hide, show, visible, theme, tooltip
"""

from __future__ import annotations

from typing import Any

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CheckboxView,
    ColorPickerView,
    ControlEvent,
    DropdownUI,
    DropdownView,
    EGroupVariant,
    EIconMaterial,
    EIconUC,
    FileChooserView,
    GroupUI,
    GroupView,
    MenuView,
    ParamsView,
    SceneView,
    SliderUI,
    SliderView,
    StackView,
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

    async def on_params(self, _state: Any, event: ControlEvent) -> None:
        if event.key == "radius":
            self._apply_radius(float(event.value))
        elif event.key == "mode":
            opacity = {"Solid": 0.9, "Translucent": 0.35, "Hidden": 0.0}
            self.viz.update("ball", opacity=opacity[str(event.value)])
            self.viz.flush()
        self._set_annotation(f"ParamsView: {event.key} = {event.value}")

    async def on_theme_dark(self, _value: None, _event: ControlEvent) -> None:
        self.viz.set_theme("dark")
        self._set_annotation("Theme: Dark")

    async def on_theme_compact(self, _value: None, _event: ControlEvent) -> None:
        self.viz.set_theme("compact")
        self._set_annotation("Theme: Compact")

    async def on_name(self, value: str, _event: ControlEvent) -> None:
        self._set_annotation(f"Name: {value}")

    async def on_notes(self, value: str, _event: ControlEvent) -> None:
        self._set_annotation(f"Notes: {value}")

    async def on_file(self, value: str, _event: ControlEvent) -> None:
        self._set_annotation(f"File: `{value}`")

    async def on_toggle_tooltips(self, value: bool, _event: ControlEvent) -> None:
        """Show/hide every framework tooltip page-wide (Help menu option)."""
        self.viz.set_tooltips_enabled(bool(value))
        state = "on" if value else "off"
        self._set_annotation(f"Tooltips {state} — reopen **Help** to switch them back.")

    async def on_visibility_appearance(self, value: bool, _event: ControlEvent) -> None:
        """Hide/show a whole ``GroupView`` pane (title included)."""
        self.viz.set_control_visible(self._appearance_group.id, bool(value))
        self._set_annotation(f"Appearance panel {'shown' if value else 'hidden'}.")

    async def on_visibility_wireframe(self, value: bool, _event: ControlEvent) -> None:
        """Hide/show one control: the group's other rows close up the gap."""
        self.viz.set_control_visible("wireframe", bool(value))
        self._set_annotation(
            f"Wireframe control {'shown' if value else 'hidden'} "
            "(the Appearance rows close up)."
        )

    async def on_visibility_params_radius(
        self, value: bool, _event: ControlEvent
    ) -> None:
        """Hide/show one ``ParamsView`` row — its key label goes with it."""
        self._params_view.set_visible("radius", bool(value))
        self._set_annotation(f"Params row 'radius' {'shown' if value else 'hidden'}.")

    async def on_visibility_params_shape(
        self, value: bool, _event: ControlEvent
    ) -> None:
        """Hide/show the nested ``Shape`` sub-panel of the ``ParamsView``."""
        self._params_view.set_visible("shape", bool(value))
        self._set_annotation(f"Params group 'Shape' {'shown' if value else 'hidden'}.")

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
            tooltip="Click to type; buttons, arrow keys, and the scroll wheel step the value",
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
        # A ParamsView with a nested sub-group; the ``shape`` GroupUI is
        # explicitly tiny (the depth-0 default would be small).
        params_view = ParamsView(
            {
                "radius": self._radius,
                "mode": "Solid",
                "shape": {"detail": 24, "smooth": True},
            },
            styles={
                "radius": SliderUI(
                    min=0.3, max=3.0, step=0.05, tooltip="Scale the sphere"
                ),
                "mode": DropdownUI(
                    options=["Solid", "Translucent", "Hidden"],
                    tooltip="Switch the material",
                ),
                "shape": GroupUI(
                    title="Shape",
                    variant=EGroupVariant.TINY,
                    tooltip="Nested shape settings",
                ),
            },
            on_change=self.on_params,
        )
        # A permanent menu bar with one "Help" menu whose single option toggles
        # every tooltip on the page (no layout re-push: ``ui_options`` message).
        help_bar = MenuView(
            mode="bar",
            children=[
                MenuView(
                    "Help",
                    [
                        CheckboxView(
                            "show_tooltips",
                            label="Show tooltips",
                            value=True,
                            tooltip="Hide or show every tooltip on this page",
                            on_change=self.on_toggle_tooltips,
                        ),
                    ],
                    trigger_icon=EIconMaterial.HELP,
                    tooltip="Help topics",
                ),
                MenuView(
                    "Theme",
                    [
                        ButtonView(
                            "theme_dark",
                            label="Dark",
                            tooltip="Dark theme",
                            on_click=self.on_theme_dark,
                        ),
                        ButtonView(
                            "theme_compact",
                            label="Compact",
                            tooltip="Compact dense theme",
                            on_click=self.on_theme_compact,
                        ),
                    ],
                    trigger_icon=EIconMaterial.PALETTE,
                    tooltip="Switch the whole UI theme",
                ),
                MenuView(
                    "Visibility",
                    [
                        CheckboxView(
                            "vision_appearance",
                            label="Appearance panel",
                            value=True,
                            tooltip="Hide the whole group pane, title included",
                            on_change=self.on_visibility_appearance,
                        ),
                        CheckboxView(
                            "vision_wireframe",
                            label="Wireframe control",
                            value=True,
                            tooltip="Hide one control inside the Appearance group",
                            on_change=self.on_visibility_wireframe,
                        ),
                        CheckboxView(
                            "vision_params_radius",
                            label="Params: Radius row",
                            value=True,
                            tooltip="Hide one Parameters row (key label + control)",
                            on_change=self.on_visibility_params_radius,
                        ),
                        CheckboxView(
                            "vision_params_shape",
                            label="Params: Shape group",
                            value=True,
                            tooltip="Hide the nested Shape sub-panel",
                            on_change=self.on_visibility_params_shape,
                        ),
                    ],
                    trigger_icon=EIconMaterial.VISIBILITY,
                    tooltip="Hide/show panels, controls and Parameters rows",
                ),
            ],
        )
        # Named locals for the two overlay panes: the Visibility menu toggles the
        # Appearance group by view id (`set_control_visible` resolves a control id
        # first and then a view/group id), so no layout re-push is needed.
        appearance_group = GroupView(
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
        )
        text_group = GroupView(
            "Text & files",
            [notes_view, data_file_view],
            icon="material:edit",  # raw-string icon (same as the enum form)
            tooltip="Free-form notes and a file picker",
            position="top-right",
        )
        self._appearance_group = appearance_group
        self._params_view = params_view
        self.viz.set_layout(
            StackView(
                "vertical",
                [
                    help_bar,
                    SceneView(
                        "",
                        overlay=[
                            appearance_group,
                            text_group,
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
                                tooltip="Actions on the sphere and the annotation",
                                position="top-left",
                            ),
                            GroupView(
                                "Parameters",
                                [params_view],
                                icon=EIconMaterial.TUNE,
                                tooltip="A ParamsView with a nested group (variant=TINY)",
                                position="bottom-left",
                            ),
                        ],
                    ),
                ],
            )
        )


if __name__ == "__main__":
    AllControlsApp().run()
````

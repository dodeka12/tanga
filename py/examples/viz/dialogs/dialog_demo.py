# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""dialog_demo.py — A titled dialog whose body holds view-based controls.

Demonstrates :meth:`show_dialog <pytanga.viz.Visualizer.show_dialog>`: a dialog
whose content is a ``StackView`` of control views — a slider that edits the
sphere's opacity, a multi-line ``TextAreaView`` that fills the remaining width
(``preferred_width=Size.fr(1)``) beside a "Close" button, and a fixed dialog
``width=Size.px(600)``.  A menu bar at the top reopens the dialog after it has
been closed, and also opens a **modal** dialog (``dismissable=False``) whose
dimmed backdrop blocks the scene.

The settings dialog can be dismissed three ways:

- clicking the built-in ✕ (fires ``on_close``),
- clicking the "Close" button inside the content (wired to ``remove_dialog``),
- or programmatically via ``remove_dialog``.

Run with:  uv run python py/examples/viz/dialogs/dialog_demo.py

Keywords: dialog, modal, show_dialog, remove_dialog, on_close, StackView, flex, Size
"""

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    MenuView,
    SceneView,
    Size,
    SliderView,
    StackView,
    TextAreaView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Dialog")
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.4
)

_settings_id: str | None = None


async def _on_opacity(value, _event):
    viz.update("sphere", opacity=float(value))
    viz.flush()


async def _on_close(_value, _event):
    print("Dialog closed (on_close fired)")


async def _on_close_button(_value, _event):
    if _settings_id:
        viz.remove_dialog(_settings_id)


def _settings_content() -> StackView:
    return StackView(
        "vertical",
        [
            SliderView(
                "dlg_opacity",
                label="Opacity",
                min=0.05,
                max=1.0,
                value=0.4,
                on_change=_on_opacity,
            ),
            StackView(
                "horizontal",
                [
                    TextAreaView(
                        "dlg_notes",
                        label="Notes",
                        value="Edit me",
                        preferred_width=Size.fr(1),
                    ),
                    ButtonView("dlg_close", label="Close", on_click=_on_close_button),
                ],
                gap=8,
                align="center",
            ),
        ],
    )


async def _on_show_dialog(_value, _event):
    global _settings_id
    if _settings_id:
        viz.remove_dialog(_settings_id)
    _settings_id = await viz.show_dialog_async(
        _settings_content(),
        title="Scene settings",
        on_close=_on_close,
        width=Size.px(600),
    )
    print("Dialog re-opened from the menu bar")


async def _on_show_modal(_value, _event):
    modal_id: str | None = None

    async def _on_ok(_v, _e):
        if modal_id:
            viz.remove_dialog(modal_id)

    modal_id = await viz.show_dialog_async(
        StackView("vertical", [ButtonView("modal_ok", label="OK", on_click=_on_ok)]),
        title="Notice",
        dismissable=False,
    )


bar = MenuView(
    mode="bar",
    children=[
        ButtonView("bar_show", label="Show dialog", on_click=_on_show_dialog),
        ButtonView("bar_modal", label="Modal dialog", on_click=_on_show_modal),
    ],
)

viz.show(layout=StackView("vertical", [bar, SceneView("")]))

_settings_id = viz.show_dialog(
    _settings_content(),
    title="Scene settings",
    on_close=_on_close,
    width=Size.px(600),
)
print("Dialog shown — use the menu bar to reopen it or show a modal dialog.")

viz.wait()

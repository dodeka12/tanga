# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""file_chooser_dialog.py — A file-selection view, embedded and in a dialog box.

Shows the bare ``FileChooserView`` (an embedded directory listing with no path
field or browse button) inside a split-view layout, and a ``FileChooserDialog``
— a full dialog with a path line and OK/Cancel — shown via ``show_dialog``.
Selecting a file fills the dialog's path line; ``OK`` fires ``on_accept``.

Run with:  uv run python py/examples/viz/ui/dialogs/file_chooser_dialog.py

Keywords: dialog, file chooser, FileChooserDialog, FileChooserView, show_dialog
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    FileChooserDialog,
    FileChooserView,
    SceneView,
    SplitView,
    StackView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — File Chooser Dialog")
viz.add(Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff")

_dialog_id: str | None = None


async def _on_file(path: str, _event) -> None:
    print("Selected:", path)


async def _on_show_dialog(_value, _event) -> None:
    global _dialog_id
    if _dialog_id:
        viz.remove_dialog(_dialog_id)
    _dialog_id = await viz.show_dialog_async(
        FileChooserDialog("dlg_file", on_accept=_on_file),
        title="Select a file",
    )


layout = SplitView(
    orientation="horizontal",
    children=[
        SceneView(""),
        StackView(
            "vertical",
            [
                FileChooserView("embedded_file", on_change=_on_file),
                ButtonView(
                    "show_dialog",
                    label="Open file dialog",
                    on_click=_on_show_dialog,
                ),
            ],
        ),
    ],
)

viz.show(layout=layout)
viz.wait()

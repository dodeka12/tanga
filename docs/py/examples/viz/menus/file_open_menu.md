# A menu bar with a File → Open… file dialog

**Keywords:** menu · menu bar · submenu · file dialog · FileChooserDialog · annotation

Shows a permanent `mode="bar"` menu at the top of the layout whose "File"
submenu holds an "Open…" item.  Choosing it opens a `FileChooserDialog`;
selecting a file fills the dialog's path line, and `OK` prints the chosen
path in the annotation panel.

## Run

```bash
uv run python py/examples/viz/menus/file_open_menu.py
```

## Source

[`viz/menus/file_open_menu.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/menus/file_open_menu.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""file_open_menu.py — A menu bar with a File → Open… file dialog.

Shows a permanent ``mode="bar"`` menu at the top of the layout whose "File"
submenu holds an "Open…" item.  Choosing it opens a ``FileChooserDialog``;
selecting a file fills the dialog's path line, and ``OK`` prints the chosen
path in the annotation panel.

Run with:  uv run python py/examples/viz/menus/file_open_menu.py

Keywords: menu, menu bar, submenu, file dialog, FileChooserDialog, annotation
"""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    FileChooserDialog,
    MenuView,
    SceneView,
    StackView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — File Open Menu")
viz.add(
    Sphere(Point(0, 0, 0), radius=2), entity_id="sphere", color="#4488ff", opacity=0.4
)

_dialog_id: str | None = None


async def _on_file(path: str, _event) -> None:
    viz.set_annotation(f"Selected: `{path}`")


async def _on_open(_value, _event) -> None:
    global _dialog_id
    if _dialog_id:
        viz.remove_dialog(_dialog_id)
    _dialog_id = await viz.show_dialog_async(
        FileChooserDialog("open_file", on_accept=_on_file),
        title="Open file",
    )


# A permanent horizontal menu bar with a "File" drop-down submenu.
bar = MenuView(
    mode="bar",
    children=[
        MenuView(
            "File",
            [
                ButtonView("file_open", label="Open…", on_click=_on_open),
            ],
        ),
    ],
)

viz.show(layout=StackView("vertical", [bar, SceneView("")]))
viz.wait()
````
